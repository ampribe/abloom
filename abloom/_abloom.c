#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include <math.h>
#include <string.h>
#include "../murmur3.h"

// SBBF constants: 256-bit blocks (8 x 32-bit words)
#define BLOCK_BITS 256
#define BLOCK_BYTES 32
#define BLOCK_WORDS 8
#define BITS_PER_WORD 32

// Salt constants from Parquet spec
static const uint32_t SALT[8] = {
    0x47b6137bU, 0x44974d91U, 0x8824ad5bU, 0xa2b7289dU,
    0x705495c7U, 0x2df1424bU, 0x9efc4947U, 0x5c6bfb31U
};

typedef struct {
    PyObject_HEAD
    uint32_t *blocks;
    uint64_t block_count;
    uint64_t block_mask;
    uint64_t item_count;
    uint64_t capacity;
    double fp_rate;
} BloomFilter;

static uint64_t next_power_of_2(uint64_t n) {
    if (n == 0) return 1;
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
    if (capacity == 0) capacity = 1;
    if (fp_rate <= 0.0 || fp_rate >= 1.0) {
        fp_rate = 0.01;
    }
    
    // For SBBF with k=8, we need approximately:
    // bits_per_item = -log2(fp_rate) * 1.44
    // But SBBF has slightly worse FPR due to blocking, so add ~20-30%
    double bits_per_item = -log2(fp_rate) * 1.44 * 1.25;
    
    // Minimum of 8 bits per item for k=8 to make sense
    if (bits_per_item < 8.0) bits_per_item = 8.0;
    
    uint64_t total_bits = (uint64_t)ceil(capacity * bits_per_item);
    uint64_t min_blocks = (total_bits + BLOCK_BITS - 1) / BLOCK_BITS;
    
    return next_power_of_2(min_blocks);
}

static inline void bloom_insert(BloomFilter *bf, uint64_t hash) {
    // Upper 32 bits select the block
    uint64_t block_idx = (hash >> 32) & bf->block_mask;
    uint32_t h_low = (uint32_t)hash;
    
    uint32_t *block = &bf->blocks[block_idx * BLOCK_WORDS];
    
    // Set one bit per word using salt multiplication
    for (int i = 0; i < BLOCK_WORDS; i++) {
        uint32_t bit_pos = (h_low * SALT[i]) >> 27;  // Top 5 bits = 0-31
        block[i] |= (1U << bit_pos);
    }
}

static inline int bloom_check(BloomFilter *bf, uint64_t hash) {
    uint64_t block_idx = (hash >> 32) & bf->block_mask;
    uint32_t h_low = (uint32_t)hash;
    
    uint32_t *block = &bf->blocks[block_idx * BLOCK_WORDS];
    
    for (int i = 0; i < BLOCK_WORDS; i++) {
        uint32_t bit_pos = (h_low * SALT[i]) >> 27;
        if (!(block[i] & (1U << bit_pos))) {
            return 0;
        }
    }
    return 1;
}

static int get_hash(PyObject *item, uint64_t *out_hash) {
    uint64_t hash[2];
    
    if (PyBytes_Check(item)) {
        MurmurHash3_x64_128(PyBytes_AS_STRING(item), 
                           PyBytes_GET_SIZE(item), 0, hash);
    } else if (PyUnicode_Check(item)) {
        if (PyUnicode_READY(item) < 0) return -1;
        MurmurHash3_x64_128(PyUnicode_DATA(item),
                           PyUnicode_GET_LENGTH(item) * PyUnicode_KIND(item),
                           0, hash);
    } else if (PyLong_Check(item)) {
        long long val = PyLong_AsLongLong(item);
        if (val == -1 && PyErr_Occurred()) return -1;
        MurmurHash3_x64_128(&val, sizeof(val), 0, hash);
    } else {
        PyErr_SetString(PyExc_TypeError, "Item must be bytes, str, or int");
        return -1;
    }
    
    *out_hash = hash[0];  // Just use first 64 bits
    return 0;
}

static PyObject* BloomFilter_add(BloomFilter *self, PyObject *item) {
    uint64_t hash;
    if (get_hash(item, &hash) < 0) return NULL;
    
    bloom_insert(self, hash);
    self->item_count++;
    
    Py_RETURN_NONE;
}

static int BloomFilter_contains(BloomFilter *self, PyObject *item) {
    uint64_t hash;
    if (get_hash(item, &hash) < 0) return -1;
    
    return bloom_check(self, hash);
}

static Py_ssize_t BloomFilter_len(BloomFilter *self) {
    return (Py_ssize_t)self->item_count;
}

static PyObject* BloomFilter_get_capacity(BloomFilter *self, void *closure) {
    return PyLong_FromUnsignedLongLong(self->capacity);
}

static PyObject* BloomFilter_get_fp_rate(BloomFilter *self, void *closure) {
    return PyFloat_FromDouble(self->fp_rate);
}

static PyObject* BloomFilter_get_k(BloomFilter *self, void *closure) {
    return PyLong_FromLong(BLOCK_WORDS);  // Always 8 for SBBF
}

static PyObject* BloomFilter_get_byte_count(BloomFilter *self, void *closure) {
    uint64_t bytes = self->block_count * BLOCK_BYTES;
    return PyLong_FromUnsignedLongLong(bytes);
}

static PyObject* BloomFilter_get_bit_count(BloomFilter *self, void *closure) {
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

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "K|d", kwlist, 
                                     &capacity, &fp_rate)) {
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
    self->item_count = 0;

    size_t num_bytes = self->block_count * BLOCK_BYTES;
    self->blocks = PyMem_Calloc(num_bytes, 1);
    if (self->blocks == NULL) {
        PyErr_NoMemory();
        return -1;
    }

    return 0;
}

static PyObject* BloomFilter_new(PyTypeObject *type, PyObject *args, 
                                  PyObject *kwds) {
    BloomFilter *self = (BloomFilter *)type->tp_alloc(type, 0);
    if (self != NULL) {
        self->blocks = NULL;
        self->block_count = 0;
        self->block_mask = 0;
        self->item_count = 0;
        self->capacity = 0;
        self->fp_rate = 0.0;
    }
    return (PyObject *)self;
}

static PyMethodDef BloomFilter_methods[] = {
    {"add", (PyCFunction)BloomFilter_add, METH_O,
     "Add an item to the bloom filter"},
    {NULL}
};

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
    {NULL}
};

static PySequenceMethods BloomFilter_as_sequence = {
    .sq_length = (lenfunc)BloomFilter_len,
    .sq_contains = (objobjproc)BloomFilter_contains,
};

static PyTypeObject BloomFilterType = {
    PyVarObject_HEAD_INIT(NULL, 0)
    .tp_name = "_abloom.BloomFilter",
    .tp_doc = "High-performance Split Block Bloom Filter",
    .tp_basicsize = sizeof(BloomFilter),
    .tp_itemsize = 0,
    .tp_flags = Py_TPFLAGS_DEFAULT,
    .tp_new = BloomFilter_new,
    .tp_init = (initproc)BloomFilter_init,
    .tp_dealloc = (destructor)BloomFilter_dealloc,
    .tp_methods = BloomFilter_methods,
    .tp_getset = BloomFilter_getsetters,
    .tp_as_sequence = &BloomFilter_as_sequence,
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
