import collections
import datetime
import decimal
import fcntl
import itertools
import mmap
import os
import struct
import sys


if sys.version_info < (3,):
    def _decode_char(b):
        return b[::-1].rstrip(b"\x00")

    def _decode_string(b):
        return b

    def _encode_char(s, size):
        return s.ljust(size, b"\x00")[size - 1::-1]

    def _encode_string(s):
        return s

    def _iteritems(d):
        return d.iteritems()

    def next(i):
        return i.next()

    _integer_types = (int, long)
    _izip = itertools.izip
    _not_null = b"\x00"
    _null = b"\x01"
    _null_terminator = b"\x00"
else:
    def _decode_char(b):
        return b[::-1].rstrip(b"\x00").decode(errors="replace")

    def _decode_string(b):
        return b.decode(errors="replace")

    def _encode_char(s, size):
        return s.encode(errors="replace").ljust(size, b"\x00")[size - 1::-1]

    def _encode_string(s):
        return s.encode(errors="replace")

    def _iteritems(d):
        return iter(d.items())

    _integer_types = (int,)
    _izip = zip
    long = int
    _not_null = 0
    _null = 1
    _null_terminator = 0
    xrange = range


_char1_struct = struct.Struct("c")
_char2_struct = struct.Struct("2s")
_char4_struct = struct.Struct("4s")
_char8_struct = struct.Struct("8s")
_char16_struct = struct.Struct("16s")
_char32_struct = struct.Struct("32s")
_char64_struct = struct.Struct("64s")
_char128_struct = struct.Struct("128s")
_char256_struct = struct.Struct("256s")
_double_struct = struct.Struct("=d")
_float_struct = struct.Struct("=f")
_int8_struct = struct.Struct("=b")
_int16_struct = struct.Struct("=h")
_int32_struct = struct.Struct("=i")
_int64_struct = struct.Struct("=q")
_uint32_struct = struct.Struct("=I")
_uint64_struct = struct.Struct("=Q")
_uint64_struct_2 = struct.Struct("=2Q")


class _MemoryMappedFile(object):
    def __init__(self):
        self.file = None
        self.writable = False
        self.size = 0
        self.data = None
        self.pos = 0

    def __del__(self):
        self.unmap()

    def map(self, path, writable, size=-1):
        self.unmap()
        self.file = os.open(path, os.O_RDWR | os.O_CREAT if writable else os.O_RDONLY)
        self.writable = writable
        self.remap(size)

    def remap(self, size=-1):
        if self.file is None:
            raise RuntimeError("File not mapped")

        try:
            if size == -1:
                size = os.fstat(self.file).st_size
            elif self.writable:
                os.ftruncate(self.file, size)

            if size == 0:
                if self.size > 0:
                    self.data.close()
                    self.size = 0
                    self.data = None
            else:
                if self.size > 0:
                    self.data.close()

                self.data = mmap.mmap(self.file, size, mmap.MAP_SHARED, mmap.PROT_READ | mmap.PROT_WRITE if self.writable else mmap.PROT_READ)
                self.size = size
        except Exception:
            self.unmap()
            raise

    def unmap(self):
        try:
            if self.file is not None:
                if self.size > 0:
                    self.data.close()
                    self.size = 0
                    self.data = None

                os.close(self.file)
                self.file = None
                self.writable = False
                self.pos = 0
        except Exception:
            pass

    def seek(self, pos):
        self._ensure(pos - self.pos)
        self.pos = pos

    def eof(self):
        return self.pos >= self.size

    def read_dict(self, result=None):
        length = self.read_uint64()

        if result is None:
            result = {}

        while length > 0:
            k = self.read_string()
            v = self.read_string()
            result[k] = v
            length -= 1

        return result

    def read_string(self):
        length = self.read_uint64()
        self._ensure(length)
        pos = self.pos
        result = self.data[pos : pos + length]
        self.pos += length
        return _decode_string(result)

    def read_uint64(self):
        self._ensure(8)
        result = _uint64_struct.unpack_from(self.data, self.pos)[0]
        self.pos += 8
        return result

    def write(self, value, add_null=False):
        length = len(value)
        total_length = length + (1 if add_null else 0)

        if total_length == 0:
            return
        else:
            self._ensure(total_length)
            data = self.data
            pos = self.pos

            data[pos : pos + length] = value

            if add_null:
                data[pos + length] = _null_terminator

            self.pos += total_length

    def write_dict(self, value):
        self.write_uint64(len(value))

        for k, v in _iteritems(value):
            self.write_string(k)
            self.write_string(v)

    def write_string(self, value):
        value = _encode_string(str(value))
        length = len(value)
        self.write_uint64(length)
        self._ensure(length)
        pos = self.pos
        self.data[pos : pos + length] = value
        self.pos += length

    def write_uint64(self, value):
        self._ensure(8)
        _uint64_struct.pack_into(self.data, self.pos, value)
        self.pos += 8

    def truncate(self):
        self.remap(self.pos)

    def lock(self, exclusive):
        if self.file is None:
            raise RuntimeError("File not mapped")

        fcntl.flock(self.file, fcntl.LOCK_EX if exclusive else fcntl.LOCK_SH)

    def unlock(self):
        if self.file is None:
            return

        fcntl.flock(self.file, fcntl.LOCK_UN)

    def _ensure(self, length):
        pos = self.pos

        if pos + length > self.size:
            if not self.writable:
                raise EOFError("End of file reached")
            else:
                minSize = pos + length
                self.remap(minSize + (mmap.PAGESIZE - (minSize % mmap.PAGESIZE)))


class _ReadOnlyMapping(collections.Mapping):
    def __init__(self, internal):
        self._internal = internal

    def __getitem__(self, key):
        return self._internal[key]

    def __iter__(self):
        return iter(self._internal)

    def __len__(self):
        return len(self._internal)

    def __repr__(self):
        return repr(self._internal)


class _SingletonType(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(_SingletonType, cls).__call__(*args, **kwargs)

        return cls._instances[cls]


def _copy(data, index, value, size):
    data[index * size : (index + 1) * size] = value


def _decode_date(value):
    return datetime.date(1900 + (value >> 21), (value >> 17) & 0b1111, (value >> 12) & 0b11111)


def _decode_datetime(value):
    return datetime.datetime(1900 + (value >> 53), (value >> 49) & 0b1111, (value >> 44) & 0b11111,
                             (value >> 39) & 0b11111, (value >> 33) & 0b111111, (value >> 27) & 0b111111, ((value >> 17) & 0b1111111111) * 1000)


def _decode_time(value):
    return datetime.time(value >> 26, (value >> 20) & 0b111111, (value >> 14) & 0b111111, ((value >> 4) & 0b1111111111) * 1000)


def _encode_date(value):
    return ((value.year - 1900) << 21) | (value.month << 17) | (value.day << 12)


def _encode_datetime(value):
    return ((value.year - 1900) << 53) | (value.month << 49) | (value.day << 44) \
           | (value.hour << 39) | (value.minute << 33) | (value.second << 27) | ((value.microsecond // 1000) << 17)


def _encode_time(value):
    return (value.hour << 26) | (value.minute << 20) | (value.second << 14) | ((value.microsecond // 1000) << 4)


class ProcData(_SingletonType("_Singleton", (object,), {})):
    class ColumnType(object):
        BYTES     = 0x0000002
        CHAR1     = 0x0080000
        CHAR2     = 0x0100000
        CHAR4     = 0x0001000
        CHAR8     = 0x0002000
        CHAR16    = 0x0004000
        CHAR32    = 0x0200000
        CHAR64    = 0x0400000
        CHAR128   = 0x0800000
        CHAR256   = 0x1000000
        DATE      = 0x2000000
        DATETIME  = 0x0000200
        DECIMAL   = 0x8000000
        DOUBLE    = 0x0000010
        FLOAT     = 0x0000020
        INT       = 0x0000040
        INT8      = 0x0020000
        INT16     = 0x0040000
        IPV4      = 0x0008000
        LONG      = 0x0000080
        STRING    = 0x0000001
        TIME      = 0x4000000
        TIMESTAMP = 0x0010000


    class Column(collections.Sequence):
        def __init__(self, file, writable):
            self._name = file.read_string()
            self._type = file.read_uint64()

            self._type_size = {
                ProcData.ColumnType.BYTES:       8,
                ProcData.ColumnType.CHAR1:       1,
                ProcData.ColumnType.CHAR2:       2,
                ProcData.ColumnType.CHAR4:       4,
                ProcData.ColumnType.CHAR8:       8,
                ProcData.ColumnType.CHAR16:     16,
                ProcData.ColumnType.CHAR32:     32,
                ProcData.ColumnType.CHAR64:     64,
                ProcData.ColumnType.CHAR128:   128,
                ProcData.ColumnType.CHAR256:   256,
                ProcData.ColumnType.DATE:        4,
                ProcData.ColumnType.DATETIME:    8,
                ProcData.ColumnType.DECIMAL:     8,
                ProcData.ColumnType.DOUBLE:      8,
                ProcData.ColumnType.FLOAT:       4,
                ProcData.ColumnType.INT:         4,
                ProcData.ColumnType.INT8:        1,
                ProcData.ColumnType.INT16:       2,
                ProcData.ColumnType.IPV4:        4,
                ProcData.ColumnType.LONG:        8,
                ProcData.ColumnType.STRING:      8,
                ProcData.ColumnType.TIME:        4,
                ProcData.ColumnType.TIMESTAMP:   8
            }.get(self._type, None)

            if self._type_size is None:
                raise ValueError("Unknown data type: " + str(self._type))

            data_path = file.read_string()
            self._data = _MemoryMappedFile()

            if data_path:
                self._data.map(data_path, writable)
                self._size = self._data.size // self._type_size
            else:
                self._size = 0

            nulls_path = file.read_string()
            self._nulls = _MemoryMappedFile()

            if nulls_path:
                self._nulls.map(nulls_path, writable)
                self._is_nullable = True
            else:
                self._is_nullable = False

            var_data_path = file.read_string()
            self._var_data = _MemoryMappedFile()

            if var_data_path:
                self._var_data.map(var_data_path, writable)

            if self._type == ProcData.ColumnType.BYTES:
                self._var_string = False
                self._var_type = True
                self._decode_var_value = lambda var_data, start, end: b"" if start == end else struct.unpack_from(str(end - start) + "s", var_data, start)[0]
            elif self.type == ProcData.ColumnType.STRING:
                self._var_string = True
                self._var_type = True
                self._decode_var_value = lambda var_data, start, end: "" if start == end else _decode_string(struct.unpack_from(str(end - start - 1) + "s", var_data, start)[0])
            else:
                self._var_string = None
                self._var_type = False

                self._decode_value = {
                    ProcData.ColumnType.CHAR1: lambda data, index: _decode_char(_char1_struct.unpack_from(data, index)[0]),
                    ProcData.ColumnType.CHAR2: lambda data, index: _decode_char(_char2_struct.unpack_from(data, index * 2)[0]),
                    ProcData.ColumnType.CHAR4: lambda data, index: _decode_char(_char4_struct.unpack_from(data, index * 4)[0]),
                    ProcData.ColumnType.CHAR8: lambda data, index: _decode_char(_char8_struct.unpack_from(data, index * 8)[0]),
                    ProcData.ColumnType.CHAR16: lambda data, index: _decode_char(_char16_struct.unpack_from(data, index * 16)[0]),
                    ProcData.ColumnType.CHAR32: lambda data, index: _decode_char(_char32_struct.unpack_from(data, index * 32)[0]),
                    ProcData.ColumnType.CHAR64: lambda data, index: _decode_char(_char64_struct.unpack_from(data, index * 64)[0]),
                    ProcData.ColumnType.CHAR128: lambda data, index: _decode_char(_char128_struct.unpack_from(data, index * 128)[0]),
                    ProcData.ColumnType.CHAR256: lambda data, index: _decode_char(_char256_struct.unpack_from(data, index * 256)[0]),
                    ProcData.ColumnType.DATE: lambda data, index: _decode_date(_int32_struct.unpack_from(data, index * 4)[0]),
                    ProcData.ColumnType.DATETIME: lambda data, index: _decode_datetime(_int64_struct.unpack_from(data, index * 8)[0]),
                    ProcData.ColumnType.DECIMAL: lambda data, index: decimal.Decimal(_int64_struct.unpack_from(data, index * 8)[0]).scaleb(-4),
                    ProcData.ColumnType.DOUBLE: lambda data, index: _double_struct.unpack_from(data, index * 8)[0],
                    ProcData.ColumnType.FLOAT: lambda data, index: _float_struct.unpack_from(data, index * 4)[0],
                    ProcData.ColumnType.INT: lambda data, index: _int32_struct.unpack_from(data, index * 4)[0],
                    ProcData.ColumnType.INT8: lambda data, index: _int8_struct.unpack_from(data, index)[0],
                    ProcData.ColumnType.INT16: lambda data, index: _int16_struct.unpack_from(data, index * 2)[0],
                    ProcData.ColumnType.IPV4: lambda data, index: _int32_struct.unpack_from(data, index * 4)[0],
                    ProcData.ColumnType.LONG: lambda data, index: _int64_struct.unpack_from(data, index * 8)[0],
                    ProcData.ColumnType.TIME: lambda data, index: _decode_time(_uint32_struct.unpack_from(data, index * 4)[0]),
                    ProcData.ColumnType.TIMESTAMP: lambda data, index: _int64_struct.unpack_from(data, index * 8)[0]
                }[self._type]

                self._decode_multiple = {
                    ProcData.ColumnType.CHAR1: lambda data, index, count: [_decode_char(value) for value in struct.unpack_from(str(count) + "c", data, index)],
                    ProcData.ColumnType.CHAR2: lambda data, index, count: [_decode_char(value) for value in struct.unpack_from("2s" * count, data, index * 2)],
                    ProcData.ColumnType.CHAR4: lambda data, index, count: [_decode_char(value) for value in struct.unpack_from("4s" * count, data, index * 4)],
                    ProcData.ColumnType.CHAR8: lambda data, index, count: [_decode_char(value) for value in struct.unpack_from("8s" * count, data, index * 8)],
                    ProcData.ColumnType.CHAR16: lambda data, index, count: [_decode_char(value) for value in struct.unpack_from("16s" * count, data, index * 16)],
                    ProcData.ColumnType.CHAR32: lambda data, index, count: [_decode_char(value) for value in struct.unpack_from("32s" * count, data, index * 32)],
                    ProcData.ColumnType.CHAR64: lambda data, index, count: [_decode_char(value) for value in struct.unpack_from("64s" * count, data, index * 64)],
                    ProcData.ColumnType.CHAR128: lambda data, index, count: [_decode_char(value) for value in struct.unpack_from("128s" * count, data, index * 128)],
                    ProcData.ColumnType.CHAR256: lambda data, index, count: [_decode_char(value) for value in struct.unpack_from("256s" * count, data, index * 256)],
                    ProcData.ColumnType.DATE: lambda data, index, count: [_decode_date(value) for value in struct.unpack_from("=" + str(count) + "i", data, index * 4)],
                    ProcData.ColumnType.DATETIME: lambda data, index, count: [_decode_datetime(value) for value in struct.unpack_from("=" + str(count) + "q", data, index * 8)],
                    ProcData.ColumnType.DECIMAL: lambda data, index, count: [decimal.Decimal(value).scaleb(-4) for value in struct.unpack_from("=" + str(count) + "q", data, index * 8)],
                    ProcData.ColumnType.DOUBLE: lambda data, index, count: list(struct.unpack_from("=" + str(count) + "d", data, index * 8)),
                    ProcData.ColumnType.FLOAT: lambda data, index, count: list(struct.unpack_from("=" + str(count) + "f", data, index * 4)),
                    ProcData.ColumnType.INT: lambda data, index, count: list(struct.unpack_from("=" + str(count) + "i", data, index * 4)),
                    ProcData.ColumnType.INT8: lambda data, index, count: list(struct.unpack_from("=" + str(count) + "b", data, index)),
                    ProcData.ColumnType.INT16: lambda data, index, count: list(struct.unpack_from("=" + str(count) + "h", data, index * 2)),
                    ProcData.ColumnType.IPV4: lambda data, index, count: list(struct.unpack_from("=" + str(count) + "i", data, index * 4)),
                    ProcData.ColumnType.LONG: lambda data, index, count: list(struct.unpack_from("=" + str(count) + "q", data, index * 8)),
                    ProcData.ColumnType.TIME: lambda data, index, count: [_decode_time(value) for value in struct.unpack_from("=" + str(count) + "I", data, index * 4)],
                    ProcData.ColumnType.TIMESTAMP: lambda data, index, count: list(struct.unpack_from("=" + str(count) + "q", data, index * 8))
                }[self._type]

        @property
        def name(self):
            return self._name

        @property
        def type(self):
            return self._type

        @property
        def is_nullable(self):
            return self._is_nullable

        @property
        def size(self):
            return self._size

        def __getitem__(self, index):
            if isinstance(index, _integer_types):
                size = self._size

                if index < 0:
                    index += size

                if index < 0 or index >= size:
                    raise IndexError("Index out of range: " + str(index))

                if not self._var_type:
                    if self._is_nullable:
                        return None if self._nulls.data[index] == _null else self._decode_value(self._data.data, index)
                    else:
                        return self._decode_value(self._data.data, index)
                else:
                    if self._is_nullable and self._nulls.data[index] == _null:
                        return None
                    else:
                        var_data = self._var_data

                        if index < size - 1:
                            positions = _uint64_struct_2.unpack_from(self._data.data, index * 8)
                        else:
                            positions = (_uint64_struct.unpack_from(self._data.data, index * 8)[0], var_data.size)

                        return self._decode_var_value(var_data.data, positions[0], positions[1])
            elif isinstance(index, slice):
                if index.step is None or index.step == 1:
                    size = self._size
                    indices = index.indices(size)
                    start = indices[0]
                    stop = indices[1]

                    if start == stop:
                        return []

                    if not self._var_type:
                        result = self._decode_multiple(self._data.data, start, stop - start)
                    else:
                        var_data = self._var_data
                        decode_var_value = self._decode_var_value

                        if (stop < size):
                            positions = struct.unpack_from("=" + str(stop - start + 1) + "Q", self._data.data, start * 8)
                        else:
                            positions = list(struct.unpack_from("=" + str(stop - start) + "Q", self._data.data, start * 8))
                            positions.append(var_data.size)

                        result = [decode_var_value(var_data.data, positions[i], positions[i + 1]) for i in xrange(0, len(positions) - 1)]

                    if self._is_nullable:
                        for i, null in enumerate(struct.unpack_from(str(stop - start) + "c", self._nulls.data, start)):
                            if null == _null:
                                result[i] = None

                    return result
                else:
                    return [self[i] for i in xrange(*index.indices(self._size))]
            else:
                raise TypeError("Invalid index specified: " + str(index))

        def __iter__(self):
            for i in xrange(0, self._size, 1024):
                for value in self[i:i + 1024]:
                    yield value

        def __len__(self):
            return self._size


    class InputColumn(Column):
        def __init__(self, file):
            super(ProcData.InputColumn, self).__init__(file, False)


    class OutputColumn(Column):
        def __init__(self, file):
            super(ProcData.OutputColumn, self).__init__(file, True)
            self._pos = 0

            if not self._var_type:
                self._encode_value = {
                    ProcData.ColumnType.CHAR1: lambda data, index, value: _char1_struct.pack_into(data, index, _encode_char(value, 1)),
                    ProcData.ColumnType.CHAR2: lambda data, index, value: _char2_struct.pack_into(data, index * 2, _encode_char(value, 2)),
                    ProcData.ColumnType.CHAR4: lambda data, index, value: _char4_struct.pack_into(data, index * 4, _encode_char(value, 4)),
                    ProcData.ColumnType.CHAR8: lambda data, index, value: _char8_struct.pack_into(data, index * 8, _encode_char(value, 8)),
                    ProcData.ColumnType.CHAR16: lambda data, index, value: _char16_struct.pack_into(data, index * 16, _encode_char(value, 16)),
                    ProcData.ColumnType.CHAR32: lambda data, index, value: _char32_struct.pack_into(data, index * 32, _encode_char(value, 32)),
                    ProcData.ColumnType.CHAR64: lambda data, index, value: _char64_struct.pack_into(data, index * 64, _encode_char(value, 64)),
                    ProcData.ColumnType.CHAR128: lambda data, index, value: _char128_struct.pack_into(data, index * 128, _encode_char(value, 128)),
                    ProcData.ColumnType.CHAR256: lambda data, index, value: _char256_struct.pack_into(data, index * 256, _encode_char(value, 256)),
                    ProcData.ColumnType.DATE: lambda data, index, value: _int32_struct.pack_into(data, index * 4, _encode_date(value)),
                    ProcData.ColumnType.DATETIME: lambda data, index, value: _int64_struct.pack_into(data, index * 8, _encode_datetime(value)),
                    ProcData.ColumnType.DECIMAL: lambda data, index, value: _int64_struct.pack_into(data, index * 8, long(value * 10000)),
                    ProcData.ColumnType.DOUBLE: lambda data, index, value: _double_struct.pack_into(data, index * 8, value),
                    ProcData.ColumnType.FLOAT: lambda data, index, value: _float_struct.pack_into(data, index * 4, value),
                    ProcData.ColumnType.INT: lambda data, index, value: _int32_struct.pack_into(data, index * 4, value),
                    ProcData.ColumnType.INT8: lambda data, index, value: _int8_struct.pack_into(data, index, value),
                    ProcData.ColumnType.INT16: lambda data, index, value: _int16_struct.pack_into(data, index * 2, value),
                    ProcData.ColumnType.IPV4: lambda data, index, value: _int32_struct.pack_into(data, index * 4, value),
                    ProcData.ColumnType.LONG: lambda data, index, value: _int64_struct.pack_into(data, index * 8, value),
                    ProcData.ColumnType.TIME: lambda data, index, value: _uint32_struct.pack_into(data, index * 4, _encode_time(value)),
                    ProcData.ColumnType.TIMESTAMP: lambda data, index, value: _int64_struct.pack_into(data, index * 8, value)
                }[self._type]

        def __setitem__(self, index, value):
            if self._var_type:
                raise RuntimeError("Cannot set values in variable-length column")

            if isinstance(index, slice):
                data = self._data.data
                encode_value = self._encode_value
                ii = iter(xrange(*index.indices(self._size)))
                vi = iter(value)

                if self._is_nullable:
                    nulls = self._nulls.data

                    for i, v in _izip(ii, vi):
                        if v is None:
                            nulls[i] = _null
                        else:
                            nulls[i] = _not_null
                            encode_value(data, i, v)
                else:
                    for i, v in _izip(ii, vi):
                        encode_value(data, i, v)

                try:
                    next(ii)
                    raise IndexError("Incorrect slice assignment size")
                except StopIteration:
                    pass

                try:
                    next(vi)
                    raise IndexError("Incorrect slice assignment size")
                except StopIteration:
                    pass
            elif isinstance(index, _integer_types):
                size = self._size

                if index < 0:
                    index += size

                if index < 0 or index >= size:
                    raise IndexError("Index out of range: " + str(index))

                if self._is_nullable:
                    if value is None:
                        self._nulls.data[index] = _null
                    else:
                        self._nulls.data[index] = _not_null
                        self._encode_value(self._data.data, index, value)
                else:
                    self._encode_value(self._data.data, index, value)
            else:
                raise TypeError("Invalid index specified: " + str(index))

        def append(self, value):
            index = self._pos

            if index >= self._size:
                raise IndexError("Insufficient table size")

            var_string = self._var_string

            if var_string is None:
                if self._is_nullable:
                    if value is None:
                        self._nulls.data[index] = _null
                    else:
                        self._nulls.data[index] = _not_null
                        self._encode_value(self._data.data, index, value)
                else:
                    self._encode_value(self._data.data, index, value)
            else:
                var_data = self._var_data
                _uint64_struct.pack_into(self._data.data, index * 8, var_data.pos)

                if self._is_nullable:
                    if value is None:
                        self._nulls.data[index] = _null
                    else:
                        self._nulls.data[index] = _not_null
                        var_data.write(_encode_string(value) if var_string else value, var_string)
                else:
                    var_data.write(_encode_string(value) if var_string else value, var_string)

            self._pos += 1
            return index

        def extend(self, values):
            index = self._pos
            data = self._data.data
            size = self._size
            var_string = self._var_string

            try:
                if var_string is None:
                    encode_value = self._encode_value

                    if self._is_nullable:
                        nulls = self._nulls.data

                        for value in values:
                            if index >= size:
                                raise IndexError("Insufficient table size")
                            elif value is None:
                                nulls[index] = _null
                            else:
                                nulls[index] = _not_null
                                encode_value(data, index, value)

                            index += 1
                    else:
                        for value in values:
                            if index >= size:
                                raise IndexError("Insufficient table size")
                            else:
                                encode_value(data, index, value)

                            index += 1
                else:
                    var_data = self._var_data

                    if self._is_nullable:
                        nulls = self._nulls.data

                        for value in values:
                            if index >= size:
                                raise IndexError("Insufficient table size")
                            else:
                                _uint64_struct.pack_into(data, index * 8, var_data.pos)

                                if value is None:
                                    nulls[index] = _null
                                else:
                                    nulls[index] = _not_null
                                    var_data.write(_encode_string(value) if var_string else value, var_string)

                            index += 1
                    else:
                        for value in values:
                            if index >= size:
                                raise IndexError("Insufficient table size")
                            else:
                                _uint64_struct.pack_into(data, index * 8, var_data.pos)
                                var_data.write(_encode_string(value) if var_string else value, var_string)

                            index += 1
            finally:
                self._pos = index

            return index - 1

        def _complete(self):
            if self._var_string is not None:
                self._var_data.truncate()

        def _reserve(self, size):
            self._data.remap(size * self._type_size)

            if self._is_nullable:
                self._nulls.remap(size)

            self._size = size


    class Table(collections.Sequence):
        def __init__(self, file, column_class):
            self._name = file.read_string()
            self._columns = [column_class(file) for _ in xrange(0, file.read_uint64())]
            self._column_dict = {column.name: column for column in self._columns}
            self._size = min(column.size for column in self._columns)

        @property
        def name(self):
            return self._name

        @property
        def size(self):
            return self._size

        def __getitem__(self, index):
            if isinstance(index, str):
                return self._column_dict[index]
            else:
                return self._columns[index]

        def __iter__(self):
            return iter(self._columns)

        def __len__(self):
            return len(self._columns)


    class InputTable(Table):
        def __init__(self, file):
            super(ProcData.InputTable, self).__init__(file, ProcData.InputColumn)


    class OutputTable(Table):
        def __init__(self, file):
            super(ProcData.OutputTable, self).__init__(file, ProcData.OutputColumn)

        @property
        def size(self):
            return self._size

        @size.setter
        def size(self, value):
            if value < 0:
                raise ValueError("Invalid size specified: " + str(value))

            for column in self._columns:
                column._reserve(value)

            self._size = value

        def _complete(self):
            for column in self._columns:
                column._complete()


    class DataSet(collections.Sequence):
        def __init__(self, file, table_class):
            self._tables = [table_class(file) for _ in xrange(0, file.read_uint64())]
            self._table_dict = {table.name: table for table in self._tables}

        def __getitem__(self, index):
            if isinstance(index, str):
                return self._table_dict[index]
            else:
                return self._tables[index]

        def __iter__(self):
            return iter(self._tables)

        def __len__(self):
            return len(self._tables)


    class InputDataSet(DataSet):
        def __init__(self, file):
            super(ProcData.InputDataSet, self).__init__(file, ProcData.InputTable)


    class OutputDataSet(DataSet):
        def __init__(self, file):
            super(ProcData.OutputDataSet, self).__init__(file, ProcData.OutputTable)

        def _complete(self):
            for table in self._tables:
                table._complete()


    def __init__(self):
        if "KINETICA_PCF" not in os.environ:
            raise RuntimeError("No control file specified")

        control_file = _MemoryMappedFile()
        control_file.map(os.environ["KINETICA_PCF"], False)

        version = control_file.read_uint64()

        if version not in (1, 2):
            raise ValueError("Unrecognized control file version: " + str(version))

        self._request_info = control_file.read_dict()
        control_file.read_dict(self._request_info)
        self._request_info = _ReadOnlyMapping(self._request_info)
        self._params = _ReadOnlyMapping(control_file.read_dict())
        self._bin_params = _ReadOnlyMapping(control_file.read_dict())
        self._input_data = ProcData.InputDataSet(control_file)
        self._output_data = ProcData.OutputDataSet(control_file)
        self._output_control_file_name = control_file.read_string()

        if version == 2:
            self._status_file = _MemoryMappedFile()
            self._status_file.map(control_file.read_string(), True)
        else:
            self._status_file = None

        self._status = ""
        self._results = {}
        self._bin_results = {}

    @property
    def request_info(self):
        return self._request_info

    @property
    def params(self):
        return self._params

    @property
    def bin_params(self):
        return self._bin_params

    @property
    def input_data(self):
        return self._input_data

    @property
    def output_data(self):
        return self._output_data

    @property
    def status(self):
        return self._status

    @status.setter
    def status(self, value):
        self._status = value

        if self._status_file is not None:
            self._status_file.lock(True)

            try:
                self._status_file.seek(0)
                self._status_file.write_string(value)
            finally:
                self._status_file.unlock()

    @property
    def results(self):
        return self._results

    @property
    def bin_results(self):
        return self._bin_results

    def complete(self):
        self._output_data._complete()
        control_file = _MemoryMappedFile()
        control_file.map(self._output_control_file_name, True)
        control_file.write_uint64(1)
        control_file.write_dict(self._results)
        control_file.write_dict(self._bin_results)
