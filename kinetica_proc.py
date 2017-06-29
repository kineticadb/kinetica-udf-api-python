import collections
import datetime
import decimal
import itertools
import mmap
import os
import struct

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
        return result

    def read_uint64(self):
        self._ensure(8)
        result = struct.unpack_from("=Q", self.data, self.pos)[0]
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
                data[pos + length] = "\x00"

            self.pos += total_length

    def write_dict(self, value):
        self.write_uint64(len(value))

        for k, v in value.iteritems():
            self.write_string(k)
            self.write_string(v)

    def write_string(self, value):
        length = len(value)
        self.write_uint64(length)
        self._ensure(length)
        pos = self.pos
        self.data[pos : pos + length] = value
        self.pos += length

    def write_uint64(self, value):
        self._ensure(8)
        struct.pack_into("=Q", self.data, self.pos, value)
        self.pos += 8

    def truncate(self):
        self.remap(self.pos)

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


class _Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(_Singleton, cls).__call__(*args, **kwargs)

        return cls._instances[cls]


def _copy(data, index, value, size):
    data[index * size : (index + 1) * size] = value


def _decode_date(value):
    return datetime.date(1900 + (value >> 21), (value >> 17) & 0b1111, (value >> 12) & 0b11111)


def _decode_time(value):
    return datetime.time(value >> 26, (value >> 20) & 0b111111, (value >> 14) & 0b111111, ((value >> 4) & 0b1111111111) * 1000)


def _encode_date(value):
    return ((value.year - 1900) << 21) | (value.month << 17) | (value.day << 12)


def _encode_time(value):
    return (value.hour << 26) | (value.minute << 20) | (value.second << 14) | ((value.microsecond / 1000) << 4)


class ProcData(object):
    __metaclass__ = _Singleton

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


    class Column(object):
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
                self._size = self._data.size / self._type_size
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
                self._var_add_null = False
            elif self.type == ProcData.ColumnType.STRING:
                self._var_add_null = True
            else:
                self._var_add_null = None

                self._decode_value = {
                    ProcData.ColumnType.CHAR1: lambda data, index: data[index : index + 1][::-1].rstrip("\0"),
                    ProcData.ColumnType.CHAR2: lambda data, index: data[index * 2 : (index + 1) * 2][::-1].rstrip("\0"),
                    ProcData.ColumnType.CHAR4: lambda data, index: data[index * 4 : (index + 1) * 4][::-1].rstrip("\0"),
                    ProcData.ColumnType.CHAR8: lambda data, index: data[index * 8 : (index + 1) * 8][::-1].rstrip("\0"),
                    ProcData.ColumnType.CHAR16: lambda data, index: data[index * 16 : (index + 1) * 16][::-1].rstrip("\0"),
                    ProcData.ColumnType.CHAR32: lambda data, index: data[index * 32 : (index + 1) * 32][::-1].rstrip("\0"),
                    ProcData.ColumnType.CHAR64: lambda data, index: data[index * 64 : (index + 1) * 64][::-1].rstrip("\0"),
                    ProcData.ColumnType.CHAR128: lambda data, index: data[index * 128 : (index + 1) * 128][::-1].rstrip("\0"),
                    ProcData.ColumnType.CHAR256: lambda data, index: data[index * 256 : (index + 1) * 256][::-1].rstrip("\0"),
                    ProcData.ColumnType.DATE: lambda data, index: _decode_date(struct.unpack_from("=i", data, index * 4)[0]),
                    ProcData.ColumnType.DECIMAL: lambda data, index: decimal.Decimal(struct.unpack_from("=q", data, index * 8)[0]).scaleb(-4),
                    ProcData.ColumnType.DOUBLE: lambda data, index: struct.unpack_from("=d", data, index * 8)[0],
                    ProcData.ColumnType.FLOAT: lambda data, index: struct.unpack_from("=f", data, index * 4)[0],
                    ProcData.ColumnType.INT: lambda data, index: struct.unpack_from("=i", data, index * 4)[0],
                    ProcData.ColumnType.INT8: lambda data, index: struct.unpack_from("=b", data, index)[0],
                    ProcData.ColumnType.INT16: lambda data, index: struct.unpack_from("=h", data, index * 2)[0],
                    ProcData.ColumnType.IPV4: lambda data, index: struct.unpack_from("=i", data, index * 4)[0],
                    ProcData.ColumnType.LONG: lambda data, index: struct.unpack_from("=q", data, index * 8)[0],
                    ProcData.ColumnType.TIME: lambda data, index: _decode_time(struct.unpack_from("=I", data, index * 4)[0]),
                    ProcData.ColumnType.TIMESTAMP: lambda data, index: struct.unpack_from("=q", data, index * 8)[0]
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
            if isinstance(index, slice):
                return [self._iter(index)]
            elif isinstance(index, (int, long)):
                size = self._size

                if index < 0:
                    index += size

                if index < 0 or index >= size:
                    raise IndexError("Index out of range: " + str(index))

                var_add_null = self._var_add_null

                if var_add_null is None:
                    if self._is_nullable:
                        return None if self._nulls.data[index] == "\x01" else self._decode_value(self._data.data, index)
                    else:
                        return self._decode_value(self._data.data, index)
                else:
                    if self._is_nullable and nulls[index] == "\x01":
                        return None
                    else:
                        data = self._data.data
                        var_data = self._var_data
                        start = struct.unpack_from("=Q", data, index * 8)[0]

                        if index < size - 1:
                            end = struct.unpack_from("=Q", data, (index + 1) * 8)[0]
                        else:
                            end = var_data.size

                        if start == end:
                            return ""
                        else:
                            return var_data.data[start : end - (1 if var_add_null else 0)]
            else:
                raise TypeError("Invalid index specified: " + str(index))

        def __iter__(self):
            return self._iter()

        def __len__(self):
            return self._size

        def _iter(self, slice=slice(None)):
            data = self._data.data
            size = self._size
            var_add_null = self._var_add_null

            if var_add_null is None:
                decode_value = self._decode_value

                if self._is_nullable:
                    nulls = self._nulls.data
                    return (None if nulls[i] == "\x01" else decode_value(data, i) for i in xrange(*slice.indices(size)))
                else:
                    return (decode_value(data, i) for i in xrange(*slice.indices(size)))
            else:
                var_data = self._var_data
                var_data_data = var_data.data
                var_data_size = var_data.size

                def get_value(index):
                    start = struct.unpack_from("=Q", data, index * 8)[0]

                    if index < size - 1:
                        end = struct.unpack_from("=Q", data, (index + 1) * 8)[0]
                    else:
                        end = var_data_size

                    if start == end:
                        return ""
                    else:
                        return var_data_data[start : end - (1 if var_add_null else 0)]

                if self._is_nullable:
                    nulls = self._nulls.data
                    return (None if nulls[i] == "\x01" else get_value(i) for i in xrange(*slice.indices(size)))
                else:
                    return (get_value(i) for i in xrange(*slice.indices(size)))


    class InputColumn(Column):
        def __init__(self, file):
            super(ProcData.InputColumn, self).__init__(file, False)


    class OutputColumn(Column):
        def __init__(self, file):
            super(ProcData.OutputColumn, self).__init__(file, True)
            self._pos = 0

            if self._var_add_null is None:
                self._encode_value = {
                    ProcData.ColumnType.CHAR1: lambda data, index, value: _copy(data, index, value.ljust(1, "\x00")[0::-1], 1),
                    ProcData.ColumnType.CHAR2: lambda data, index, value: _copy(data, index, value.ljust(2, "\x00")[1::-1], 2),
                    ProcData.ColumnType.CHAR4: lambda data, index, value: _copy(data, index, value.ljust(4, "\x00")[3::-1], 4),
                    ProcData.ColumnType.CHAR8: lambda data, index, value: _copy(data, index, value.ljust(8, "\x00")[7::-1], 8),
                    ProcData.ColumnType.CHAR16: lambda data, index, value: _copy(data, index, value.ljust(16, "\x00")[15::-1], 16),
                    ProcData.ColumnType.CHAR32: lambda data, index, value: _copy(data, index, value.ljust(32, "\x00")[31::-1], 32),
                    ProcData.ColumnType.CHAR64: lambda data, index, value: _copy(data, index, value.ljust(64, "\x00")[63::-1], 64),
                    ProcData.ColumnType.CHAR128: lambda data, index, value: _copy(data, index, value.ljust(128, "\x00")[127::-1], 128),
                    ProcData.ColumnType.CHAR256: lambda data, index, value: _copy(data, index, value.ljust(256, "\x00")[255::-1], 256),
                    ProcData.ColumnType.DATE: lambda data, index, value: struct.pack_into("=i", data, index * 4, _encode_date(value)),
                    ProcData.ColumnType.DECIMAL: lambda data, index, value: struct.pack_into("=q", data, index * 8, value * 10000),
                    ProcData.ColumnType.DOUBLE: lambda data, index, value: struct.pack_into("=d", data, index * 8, value),
                    ProcData.ColumnType.FLOAT: lambda data, index, value: struct.pack_into("=f", data, index * 4, value),
                    ProcData.ColumnType.INT: lambda data, index, value: struct.pack_into("=i", data, index * 4, value),
                    ProcData.ColumnType.INT8: lambda data, index, value: struct.pack_into("=b", data, index, value),
                    ProcData.ColumnType.INT16: lambda data, index, value: struct.pack_into("=h", data, index * 2, value),
                    ProcData.ColumnType.IPV4: lambda data, index, value: struct.pack_into("=i", data, index * 4, value),
                    ProcData.ColumnType.LONG: lambda data, index, value: struct.pack_into("=q", data, index * 8, value),
                    ProcData.ColumnType.TIME: lambda data, index, value: struct.pack_into("=I", data, index * 4, _encode_time(value)),
                    ProcData.ColumnType.TIMESTAMP: lambda data, index, value: struct.pack_into("=q", data, index * 8, value)
                }[self._type]

        def __setitem__(self, index, value):
            if self._var_add_null is not None:
                raise RuntimeError("Cannot set values in variable-length column")

            if isinstance(index, slice):
                data = self._data.data
                encode_value = self._encode_value
                ii = iter(xrange(*index.indices(self._size)))
                vi = iter(value)

                if self._is_nullable:
                    nulls = self._nulls.data

                    for i, v in itertools.izip(ii, vi):
                        if v is None:
                            nulls[i] = "\x01"
                        else:
                            nulls[i] = "\x00"
                            encode_value(data, i, v)
                else:
                    for i, v in itertools.izip(ii, vi):
                        encode_value(data, i, v)

                try:
                    ii.next()
                    raise IndexError("Incorrect slice assignment size")
                except StopIteration:
                    pass

                try:
                    vi.next()
                    raise IndexError("Incorrect slice assignment size")
                except StopIteration:
                    pass
            elif isinstance(index, (int, long)):
                size = self._size

                if index < 0:
                    index += size

                if index < 0 or index >= size:
                    raise IndexError("Index out of range: " + str(index))

                if self._is_nullable:
                    if value is None:
                        self._nulls.data[index] = "\x01"
                    else:
                        self._nulls.data[index] = "\x00"
                        self._encode_value(self._data.data, index, value)
                else:
                    self._encode_value(self._data.data, index, value)
            else:
                raise TypeError("Invalid index specified: " + str(index))

        def append(self, value):
            index = self._pos

            if index >= self._size:
                raise IndexError("Insufficient table size")

            var_add_null = self._var_add_null

            if var_add_null is None:
                if self._is_nullable:
                    if value is None:
                        self._nulls.data[index] = "\x01"
                    else:
                        self._nulls.data[index] = "\x00"
                        self._encode_value(self._data.data, index, value)
                else:
                    self._encode_value(self._data.data, index, value)
            else:
                var_data = self._var_data
                struct.pack_into("=Q", self._data.data, index * 8, var_data.pos)

                if self._is_nullable:
                    if value is None:
                        self._nulls.data[index] = "\x01"
                    else:
                        self._nulls.data[index] = "\x00"
                        var_data.write(value, var_add_null)
                else:
                    var_data.write(value, var_add_null)

            self._pos += 1
            return index

        def extend(self, values):
            index = self._pos
            data = self._data.data
            size = self._size
            var_add_null = self._var_add_null

            try:
                if var_add_null is None:
                    encode_value = self._encode_value

                    if self._is_nullable:
                        nulls = self._nulls.data

                        for value in values:
                            if index >= size:
                                raise IndexError("Insufficient table size")
                            elif value is None:
                                nulls[index] = "\x01"
                            else:
                                nulls[index] = "\x00"
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
                                struct.pack_into("=Q", data, index * 8, var_data.pos)

                                if value is None:
                                    nulls[index] = "\x01"
                                else:
                                    nulls[index] = "\x00"
                                    var_data.write(value, var_add_null)

                            index += 1
                    else:
                        for value in values:
                            if index >= size:
                                raise IndexError("Insufficient table size")
                            else:
                                struct.pack_into("=Q", data, index * 8, var_data.pos)
                                var_data.write(value, var_add_null)

                            index += 1
            finally:
                self._pos = index

            return index - 1

        def _complete(self):
            if self._var_add_null is not None:
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

        if version != 1:
            raise ValueError("Unrecognized control file version: " + str(version))

        self._request_info = control_file.read_dict()
        control_file.read_dict(self._request_info)
        self._request_info = _ReadOnlyMapping(self._request_info)
        self._params = _ReadOnlyMapping(control_file.read_dict())
        self._bin_params = _ReadOnlyMapping(control_file.read_dict())
        self._input_data = ProcData.InputDataSet(control_file)
        self._output_data = ProcData.OutputDataSet(control_file)
        self._output_control_file_name = control_file.read_string()
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