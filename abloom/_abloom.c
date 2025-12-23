#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include <math.h>
#include <string.h>

// SBBF constants: 512-bit blocks (8 x 64-bit words)
#define BLOCK_BITS 512
#define BLOCK_BYTES 64
#define BLOCK_WORDS 8
#define BITS_PER_WORD 64

// Salt constants from Parquet spec
static const uint32_t SALT[8] = {0x47b6137bU, 0x44974d91U, 0x8824ad5bU,
                                 0xa2b7289dU, 0x705495c7U, 0x2df1424bU,
                                 0x9efc4947U, 0x5c6bfb31U};

typedef struct {
  PyObject_HEAD uint64_t *blocks;
  uint64_t block_count;
  uint64_t block_mask;
  uint64_t capacity;
  double fp_rate;
} BloomFilter;

static const float SBBF512_LUT[] = {
    3.2304f,  3.8302f,  4.3978f,  4.9555f,  5.5148f,  6.0828f,  6.6644f,
    7.2634f,  7.8830f,  8.5260f,  9.1952f,  9.8929f,  10.6217f, 11.3841f,
    12.1826f, 13.0199f, 13.8988f, 14.8220f, 15.7926f, 16.8139f, 17.8892f,
    19.0222f, 20.2168f, 21.4771f, 22.8076f, 24.2130f, 25.6984f, 27.2693f,
    28.9318f, 30.6921f, 32.5573f, 34.5347f, 36.6325f, 38.8595f, 41.2251f,
    43.7396f, 46.4143f, 49.2614f, 52.2942f};
#define SBBF512_LUT_SIZE 39

static inline uint64_t mix64(uint64_t x) {
  x ^= x >> 33;
  x *= 0xff51afd7ed558ccdULL;
  x ^= x >> 33;
  x *= 0xc4ceb9fe1a85ec53ULL;
  x ^= x >> 33;
  return x;
}

static uint64_t next_power_of_2(uint64_t n) {
  if (n == 0)
    return 1;
  n--;
  n |= n >> 1;
  n |= n >> 2;
  n |= n >> 4;
  n |= n >> 8;
  n |= n >> 16;
  n |= n >> 32;
  return n + 1;
}

static uint64_t calculate_block_count(uint64_t capacity, double fp_rate) {
  if (capacity == 0)
    capacity = 1;

  double x = -log2(fp_rate);

  double bits_per_item;
  if (x <= 1.0) {
    bits_per_item = SBBF512_LUT[0];
  } else if (x >= 20.0) {
    double slope = (SBBF512_LUT[38] - SBBF512_LUT[37]) / 0.5;
    bits_per_item = SBBF512_LUT[38] + slope * (x - 20.0);
  } else {
    int idx = (int)((x - 1.0) / 0.5);
    if (idx >= SBBF512_LUT_SIZE - 1)
      idx = SBBF512_LUT_SIZE - 2;
    double t = (x - 1.0 - idx * 0.5) / 0.5;
    bits_per_item = SBBF512_LUT[idx] * (1.0 - t) + SBBF512_LUT[idx + 1] * t;
  }

  if (bits_per_item < 8.0)
    bits_per_item = 8.0;

  uint64_t total_bits = (uint64_t)ceil(capacity * bits_per_item);
  uint64_t min_blocks = (total_bits + BLOCK_BITS - 1) / BLOCK_BITS;

  return next_power_of_2(min_blocks);
}

static inline void bloom_insert(BloomFilter *bf, uint64_t hash) {
  // Upper 32 bits select the block
  uint64_t block_idx = (hash >> 32) & bf->block_mask;
  uint32_t h_low = (uint32_t)hash;

  uint64_t *block = &bf->blocks[block_idx * BLOCK_WORDS];

  uint32_t p0 = (h_low * SALT[0]) >> 26;
  uint32_t p1 = (h_low * SALT[1]) >> 26;
  uint32_t p2 = (h_low * SALT[2]) >> 26;
  uint32_t p3 = (h_low * SALT[3]) >> 26;
  uint32_t p4 = (h_low * SALT[4]) >> 26;
  uint32_t p5 = (h_low * SALT[5]) >> 26;
  uint32_t p6 = (h_low * SALT[6]) >> 26;
  uint32_t p7 = (h_low * SALT[7]) >> 26;

  block[0] |= (1ULL << p0);
  block[1] |= (1ULL << p1);
  block[2] |= (1ULL << p2);
  block[3] |= (1ULL << p3);
  block[4] |= (1ULL << p4);
  block[5] |= (1ULL << p5);
  block[6] |= (1ULL << p6);
  block[7] |= (1ULL << p7);
}

static inline int bloom_check(BloomFilter *bf, uint64_t hash) {
  uint64_t block_idx = (hash >> 32) & bf->block_mask;
  uint32_t h_low = (uint32_t)hash;
  uint64_t *block = &bf->blocks[block_idx * BLOCK_WORDS];

#define CHECK_WORD(i)                                                          \
  if (!(block[i] & (1ULL << ((h_low * SALT[i]) >> 26))))                       \
  return 0

  CHECK_WORD(0);
  CHECK_WORD(1);
  CHECK_WORD(2);
  CHECK_WORD(3);
  CHECK_WORD(4);
  CHECK_WORD(5);
  CHECK_WORD(6);
  CHECK_WORD(7);

  return 1;
#undef CHECK_WORD
}

static int get_hash(PyObject *item, uint64_t *out_hash) {
  Py_hash_t py_hash = PyObject_Hash(item);
  if (py_hash == -1 && PyErr_Occurred()) return -1;

  // try mixing first
  *out_hash = mix64((uint64_t)py_hash);
  return 0;
}

static int BloomFilter_compatible(BloomFilter *self, BloomFilter *other) {
  return self->capacity == other->capacity && self->fp_rate == other->fp_rate;
}

static PyObject *BloomFilter_richcompare(BloomFilter *self, PyObject *other, int op) {
  if (op != Py_EQ && op != Py_NE) {
    Py_RETURN_NOTIMPLEMENTED;
  }

  if (!PyObject_TypeCheck(other, Py_TYPE(self))) {
    Py_RETURN_NOTIMPLEMENTED;
  }

  BloomFilter *other_bf = (BloomFilter *)other;

  int equal = BloomFilter_compatible(self, other_bf);

  if (equal) {
    size_t num_bytes = self->block_count * BLOCK_BYTES;
    equal = (memcmp(self->blocks, other_bf->blocks, num_bytes) == 0);
  }

  if (op == Py_EQ) {
    return PyBool_FromLong(equal);
  } else {
    return PyBool_FromLong(!equal);
  }
}

static PyObject *BloomFilter_or(BloomFilter *self, PyObject *other) {
  if (!PyObject_TypeCheck(other, Py_TYPE(self))) {
    Py_RETURN_NOTIMPLEMENTED;
  }

  BloomFilter *other_bf = (BloomFilter *)other;

  if (!BloomFilter_compatible(self, other_bf)) {
    PyErr_SetString(PyExc_ValueError,
                    "BloomFilters must have the same capacity and fp_rate");
    return NULL;
  }

  BloomFilter *result =
      (BloomFilter *)Py_TYPE(self)->tp_alloc(Py_TYPE(self), 0);
  if (result == NULL) {
    return NULL;
  }

  result->block_count = self->block_count;
  result->block_mask = self->block_mask;
  result->capacity = self->capacity;
  result->fp_rate = self->fp_rate;

  size_t num_bytes = self->block_count * BLOCK_BYTES;
  result->blocks = PyMem_Malloc(num_bytes);
  if (result->blocks == NULL) {
    Py_DECREF(result);
    return PyErr_NoMemory();
  }

  uint64_t *self_blocks = self->blocks;
  uint64_t *other_blocks = other_bf->blocks;
  uint64_t *result_blocks = result->blocks;
  size_t num_words = self->block_count * BLOCK_WORDS;

  for (size_t i = 0; i < num_words; i++) {
    result_blocks[i] = self_blocks[i] | other_blocks[i];
  }

  return (PyObject *)result;
}

static PyObject *BloomFilter_ior(BloomFilter *self, PyObject *other) {
  if (!PyObject_TypeCheck(other, Py_TYPE(self))) {
    Py_RETURN_NOTIMPLEMENTED;
  }

  BloomFilter *other_bf = (BloomFilter *)other;

  if (!BloomFilter_compatible(self, other_bf)) {
    PyErr_SetString(PyExc_ValueError,
                    "BloomFilters must have the same capacity and fp_rate");
    return NULL;
  }

  uint64_t *self_blocks = self->blocks;
  uint64_t *other_blocks = other_bf->blocks;
  size_t num_words = self->block_count * BLOCK_WORDS;

  for (size_t i = 0; i < num_words; i++) {
    self_blocks[i] |= other_blocks[i];
  }

  Py_INCREF(self);
  return (PyObject *)self;
}

static int BloomFilter_bool(BloomFilter *self) {
  size_t num_words = self->block_count * BLOCK_WORDS;
  for (size_t i = 0; i < num_words; i++) {
    if (self->blocks[i] != 0) {
      return 1;
    }
  }
  return 0;
}

static PyObject *BloomFilter_clear(BloomFilter *self, PyObject *Py_UNUSED(ignored)) {
  size_t num_bytes = self->block_count * BLOCK_BYTES;
  memset(self->blocks, 0, num_bytes);
  Py_RETURN_NONE;
}

static PyObject *BloomFilter_copy(BloomFilter *self, PyObject *Py_UNUSED(ignored)) {
  BloomFilter *copy = (BloomFilter *)Py_TYPE(self)->tp_alloc(Py_TYPE(self), 0);
  if (copy == NULL) {
    return NULL;
  }

  copy->block_count = self->block_count;
  copy->block_mask = self->block_mask;
  copy->capacity = self->capacity;
  copy->fp_rate = self->fp_rate;

  size_t num_bytes = self->block_count * BLOCK_BYTES;
  copy->blocks = PyMem_Malloc(num_bytes);
  if (copy->blocks == NULL) {
    Py_DECREF(copy);
    return PyErr_NoMemory();
  }
  memcpy(copy->blocks, self->blocks, num_bytes);

  return (PyObject *)copy;
}

static PyObject *BloomFilter_update(BloomFilter *self, PyObject *iterable) {
  PyObject *iter = PyObject_GetIter(iterable);
  if (iter == NULL)
    return NULL;

  PyObject *item;
  while ((item = PyIter_Next(iter)) != NULL) {
    uint64_t hash;
    if (get_hash(item, &hash) < 0) {
      Py_DECREF(item);
      Py_DECREF(iter);
      return NULL;
    }
    bloom_insert(self, hash);
    Py_DECREF(item);
  }
  Py_DECREF(iter);

  if (PyErr_Occurred())
    return NULL;
  Py_RETURN_NONE;
}

static PyObject *BloomFilter_add(BloomFilter *self, PyObject *item) {
  uint64_t hash;
  if (get_hash(item, &hash) < 0)
    return NULL;

  bloom_insert(self, hash);

  Py_RETURN_NONE;
}

static int BloomFilter_contains(BloomFilter *self, PyObject *item) {
  uint64_t hash;
  if (get_hash(item, &hash) < 0)
    return -1;

  return bloom_check(self, hash);
}

static PyObject *BloomFilter_get_capacity(BloomFilter *self, void *closure) {
  return PyLong_FromUnsignedLongLong(self->capacity);
}

static PyObject *BloomFilter_get_fp_rate(BloomFilter *self, void *closure) {
  return PyFloat_FromDouble(self->fp_rate);
}

static PyObject *BloomFilter_get_k(BloomFilter *self, void *closure) {
  return PyLong_FromLong(BLOCK_WORDS); // Always 8 for SBBF
}

static PyObject *BloomFilter_get_byte_count(BloomFilter *self, void *closure) {
  uint64_t bytes = self->block_count * BLOCK_BYTES;
  return PyLong_FromUnsignedLongLong(bytes);
}

static PyObject *BloomFilter_get_bit_count(BloomFilter *self, void *closure) {
  uint64_t bits = self->block_count * BLOCK_BITS;
  return PyLong_FromUnsignedLongLong(bits);
}

static void BloomFilter_dealloc(BloomFilter *self) {
  if (self->blocks) {
    PyMem_Free(self->blocks);
  }
  Py_TYPE(self)->tp_free((PyObject *)self);
}

static int BloomFilter_init(BloomFilter *self, PyObject *args, PyObject *kwds) {
  static char *kwlist[] = {"capacity", "fp_rate", NULL};
  unsigned long long capacity;
  double fp_rate = 0.01;

  if (!PyArg_ParseTupleAndKeywords(args, kwds, "K|d", kwlist, &capacity,
                                   &fp_rate)) {
    return -1;
  }

  if (capacity == 0) {
    PyErr_SetString(PyExc_ValueError, "Capacity must be greater than 0");
    return -1;
  }

  if (fp_rate <= 0.0 || fp_rate >= 1.0) {
    PyErr_SetString(PyExc_ValueError,
                    "False positive rate must be between 0.0 and 1.0");
    return -1;
  }

  self->capacity = capacity;
  self->fp_rate = fp_rate;
  self->block_count = calculate_block_count(capacity, fp_rate);
  self->block_mask = self->block_count - 1;

  size_t num_bytes = self->block_count * BLOCK_BYTES;
  self->blocks = PyMem_Calloc(num_bytes, 1);
  if (self->blocks == NULL) {
    PyErr_NoMemory();
    return -1;
  }

  return 0;
}

static PyObject *BloomFilter_new(PyTypeObject *type, PyObject *args,
                                 PyObject *kwds) {
  BloomFilter *self = (BloomFilter *)type->tp_alloc(type, 0);
  if (self != NULL) {
    self->blocks = NULL;
    self->block_count = 0;
    self->block_mask = 0;
    self->capacity = 0;
    self->fp_rate = 0.0;
  }
  return (PyObject *)self;
}

static PyMethodDef BloomFilter_methods[] = {
    {"add", (PyCFunction)BloomFilter_add, METH_O,
     "Add an item to the bloom filter"},
    {"update", (PyCFunction)BloomFilter_update, METH_O,
     "Add items from an iterable to the bloom filter"},
    {"copy", (PyCFunction)BloomFilter_copy, METH_NOARGS,
     "Return a shallow copy of the bloom filter"},
    {"clear", (PyCFunction)BloomFilter_clear, METH_NOARGS,
     "Remove all items from the bloom filter"},
    {NULL}};

static PyGetSetDef BloomFilter_getsetters[] = {
    {"capacity", (getter)BloomFilter_get_capacity, NULL,
     "Expected number of items", NULL},
    {"fp_rate", (getter)BloomFilter_get_fp_rate, NULL,
     "Target false positive rate", NULL},
    {"k", (getter)BloomFilter_get_k, NULL,
     "Number of hash functions (always 8 for SBBF)", NULL},
    {"byte_count", (getter)BloomFilter_get_byte_count, NULL,
     "Memory usage in bytes", NULL},
    {"bit_count", (getter)BloomFilter_get_bit_count, NULL,
     "Total bits in filter", NULL},
    {NULL}};

static PySequenceMethods BloomFilter_as_sequence = {
    .sq_contains = (objobjproc)BloomFilter_contains,
};

static PyNumberMethods BloomFilter_as_number = {
    .nb_bool = (inquiry)BloomFilter_bool,
    .nb_or = (binaryfunc)BloomFilter_or,
    .nb_inplace_or = (binaryfunc)BloomFilter_ior,
};

static PyObject *BloomFilter_repr(BloomFilter *self) {
  PyObject *fp_obj = PyFloat_FromDouble(self->fp_rate);
  if (!fp_obj)
    return NULL;

  PyObject *repr =
      PyUnicode_FromFormat("<BloomFilter capacity=%llu fp_rate=%R>",
                           self->capacity, fp_obj);

  Py_DECREF(fp_obj);
  return repr;
}

static PyTypeObject BloomFilterType = {
    PyVarObject_HEAD_INIT(NULL, 0).tp_name = "_abloom.BloomFilter",
    .tp_doc = "High-performance Split Block Bloom Filter",
    .tp_basicsize = sizeof(BloomFilter),
    .tp_itemsize = 0,
    .tp_flags = Py_TPFLAGS_DEFAULT,
    .tp_new = BloomFilter_new,
    .tp_init = (initproc)BloomFilter_init,
    .tp_dealloc = (destructor)BloomFilter_dealloc,
    .tp_repr = (reprfunc)BloomFilter_repr,
    .tp_richcompare = (richcmpfunc)BloomFilter_richcompare,
    .tp_methods = BloomFilter_methods,
    .tp_getset = BloomFilter_getsetters,
    .tp_as_sequence = &BloomFilter_as_sequence,
    .tp_as_number = &BloomFilter_as_number,
};

static PyModuleDef abloommodule = {
    PyModuleDef_HEAD_INIT,
    .m_name = "_abloom",
    .m_doc = "High-performance Split Block Bloom Filter for Python",
    .m_size = -1,
};

PyMODINIT_FUNC PyInit__abloom(void) {
  PyObject *m;

  if (PyType_Ready(&BloomFilterType) < 0)
    return NULL;

  m = PyModule_Create(&abloommodule);
  if (m == NULL)
    return NULL;

  Py_INCREF(&BloomFilterType);
  if (PyModule_AddObject(m, "BloomFilter", (PyObject *)&BloomFilterType) < 0) {
    Py_DECREF(&BloomFilterType);
    Py_DECREF(m);
    return NULL;
  }

  return m;
}
