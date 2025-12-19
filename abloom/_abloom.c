#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include <math.h>
#include <string.h>
#include "../murmur3.h"

const uint64_t BLOCK_BITS = 512;
const uint64_t BLOCK_BYTES = 64;
const uint64_t BLOCK_SHIFT = 9;

typedef struct {
    PyObject_HEAD
    uint8_t *bitmap;
    uint64_t bit_count;
    uint32_t k;
    uint64_t item_count;
    uint64_t capacity;
    double fp_rate;
    uint64_t block_count;
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
    n++;
    return n;
}

static uint64_t calculate_optimal_bits(uint64_t capacity, double error_rate) {
    if (capacity == 0) capacity = 1;
    if (error_rate <= 0.0 || error_rate >= 1.0) {
        error_rate = 0.01;
    }
    // m = -(n * ln(p)) / (ln(2)^2)
    double m = -(double)capacity * log(error_rate) / (log(2.0) * log(2.0));
    // add 20% to adjust for blocking
    m *= 1.2;
    return next_power_of_2((uint64_t)ceil(m));
}

static uint32_t calculate_optimal_hashes(uint64_t num_bits, uint64_t capacity) {
    if (capacity == 0) capacity = 1;
    // k = (m/n) * ln(2)
    double k = ((double)num_bits / (double)capacity) * log(2.0);
    uint32_t result = (uint32_t)round(k);
    if (result > 3) {
        result -= 1;
    }
    return result > 0 ? result : 1;
}

static void bloom_insert(BloomFilter *bf, const void *data, Py_ssize_t len) {
    uint64_t hash[2];
    MurmurHash3_x64_128(data, len, 0, hash);
    
    uint64_t h1 = hash[0];
    uint64_t h2 = hash[1] | 1;  // Ensure odd for better distribution
    uint64_t block = (h1 >> 32) & (bf->block_count - 1);

    for (uint32_t i = 0; i < bf->k; i++) {
        uint64_t index = (h1 + i * h2) & (BLOCK_BITS - 1);
        bf->bitmap[block * BLOCK_BYTES + (index >> 3)] |= (1 << (index & 7));
    }
}

static int bloom_check(BloomFilter *bf, const void *data, Py_ssize_t len) {
    uint64_t hash[2];
    MurmurHash3_x64_128(data, len, 0, hash);
    
    uint64_t h1 = hash[0];
    uint64_t h2 = hash[1] | 1;
    uint64_t block = (h1 >> 32) & (bf->block_count - 1);
    
    for (uint32_t i = 0; i < bf->k; i++) {
        uint64_t index = (h1 + i * h2) & (BLOCK_BITS - 1);
        if (!(bf->bitmap[block * BLOCK_BYTES + (index >> 3)] & (1 << (index & 7)))) {
            return 0;
        }
    }
    return 1;
}

static PyObject* BloomFilter_add(BloomFilter *self, PyObject *item) {
    const void *data;
    Py_ssize_t len;
    long long val;
    if (PyBytes_Check(item)) {
        data = PyBytes_AS_STRING(item);
        len = PyBytes_GET_SIZE(item);
    } else if (PyUnicode_Check(item)) {
        if (PyUnicode_READY(item) < 0) return NULL;
        data = PyUnicode_DATA(item);
        len = PyUnicode_GET_LENGTH(item) * PyUnicode_KIND(item);
    } else if (PyLong_Check(item)) {
        val = PyLong_AsLongLong(item);
        if (val == -1 && PyErr_Occurred()) return NULL;
        data = &val;
        len = sizeof (val);
    } else {
        PyErr_SetString(PyExc_TypeError, "Item must be bytes, str, or int");
        return 0;
    }

    bloom_insert(self, data, len);
    self->item_count++;

    Py_RETURN_NONE;
}

static int BloomFilter_contains(BloomFilter *self, PyObject *item) {
    const void *data;
    Py_ssize_t len;
    long long val;
    if (PyBytes_Check(item)) {
        data = PyBytes_AS_STRING(item);
        len = PyBytes_GET_SIZE(item);
    } else if (PyUnicode_Check(item)) {
        if (PyUnicode_READY(item) < 0) return -1;
        data = PyUnicode_DATA(item);
        len = PyUnicode_GET_LENGTH(item) * PyUnicode_KIND(item);
    } else if (PyLong_Check(item)) {
        val = PyLong_AsLongLong(item);
        if (val == -1 && PyErr_Occurred()) return -1;
        data = &val;
        len = sizeof (val);
    } else {
        PyErr_SetString(PyExc_TypeError, "Item must be bytes, str, or int");
        return -1;
    }

    int result;
    result = bloom_check(self, data, len);

    return result;
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
    return PyLong_FromUnsignedLong(self->k);
}

static PyObject* BloomFilter_get_byte_count(BloomFilter *self, void *closure) {
    uint64_t bytes = self->bit_count / 8;
    return PyLong_FromUnsignedLongLong(bytes);
}

static void BloomFilter_dealloc(BloomFilter *self) {
    if (self->bitmap) {
        PyMem_Free(self->bitmap);
    }
    Py_TYPE(self)->tp_free((PyObject *)self);
}

static int BloomFilter_init(BloomFilter *self, PyObject *args, PyObject *kwds) {
    static char *kwlist[] = {"capacity", "fp_rate", NULL};
    unsigned long long capacity;
    double fp_rate = 0.01;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "K|d", kwlist, &capacity, &fp_rate)) {
        return -1;
    }

    if (capacity == 0) {
        PyErr_SetString(PyExc_ValueError, "Capacity must be greater than 0");
        return -1;
    }

    if (fp_rate <= 0.0 || fp_rate >= 1.0) {
        PyErr_SetString(PyExc_ValueError, "False positive rate must be between 0.0 and 1.0");
        return -1;
    }

    self->capacity = capacity;
    self->fp_rate = fp_rate;
    self->bit_count = calculate_optimal_bits(capacity, fp_rate);
    self->k = calculate_optimal_hashes(self->bit_count, capacity);
    self->block_count = self->bit_count >> BLOCK_SHIFT;
    self->item_count = 0;

    uint64_t num_bytes = self->bit_count / 8;
    self->bitmap = PyMem_Calloc(num_bytes, 1);
    if (self->bitmap == NULL) {
        PyErr_NoMemory();
        return -1;
    }

    return 0;
}

static PyObject* BloomFilter_new(PyTypeObject *type, PyObject *args, PyObject *kwds) {
    BloomFilter *self;
    self = (BloomFilter *)type->tp_alloc(type, 0);
    if (self != NULL) {
        self->bitmap = NULL;
        self->bit_count = 0;
        self->k = 0;
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
     "Number of hash functions", NULL},
    {"byte_count", (getter)BloomFilter_get_byte_count, NULL,
     "Memory usage in bytes", NULL},
    {NULL}
};

static PySequenceMethods BloomFilter_as_sequence = {
    .sq_length = (lenfunc)BloomFilter_len,
    .sq_contains = (objobjproc)BloomFilter_contains,
};

static PyTypeObject BloomFilterType = {
    PyVarObject_HEAD_INIT(NULL, 0)
    .tp_name = "_abloom.BloomFilter",
    .tp_doc = "High-performance Bloom filter",
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
    .m_doc = "High-performance Bloom filter for Python",
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
