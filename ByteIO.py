import contextlib
import io
import struct
import typing
import zlib
from io import BytesIO


class OffsetOutOfBounds(Exception):
    pass


class ByteIO:
    @contextlib.contextmanager
    def save_current_pos(self):
        entry = self.tell()
        yield
        self.seek(entry)

    def __bool__(self):
        return self.tell() < self.size()


    def __init__(self, file=None, path=None, byte_object=None, mode='r', copy_data_from_handle=True):

        """
        Supported file handlers
        :type byte_object: bytes
        :type path: str
        :type file: typing.IO[bytes]
        """
        if file:
            if 'w' in file.mode:
                self.file = file
            elif 'r' in file.mode and copy_data_from_handle:
                self.file = io.BytesIO(file.read())
                file.close()
            elif 'r' in file.mode and not copy_data_from_handle:
                self.file = file
        elif path:
            if 'w' in mode:
                self.file = open(path, mode + 'b')
            elif 'r' in mode:
                with open(path, mode + 'b') as f:
                    self.file = io.BytesIO(f.read())

        elif byte_object:
            self.file = io.BytesIO(byte_object)
        else:
            self.file = BytesIO()

    def __repr__(self):
        return "<ByteIO {}/{}>".format(self.tell(), self.size())

    def close(self):
        if hasattr(self.file, 'mode'):
            if 'w' in getattr(self.file, 'mode'):
                self.file.close()

    @property
    def preview(self):
        with self.save_current_pos():
            return self.read_bytes(256)


    def rewind(self, amount):
        self.file.seek(-amount, io.SEEK_CUR)

    def skip(self, amount):
        self.file.seek(amount, io.SEEK_CUR)

    def seek(self, off, pos=io.SEEK_SET):
        self.file.seek(off, pos)

    def tell(self):
        return self.file.tell()

    def size(self):
        curr_offset = self.tell()
        self.seek(0, io.SEEK_END)
        ret = self.tell()
        self.seek(curr_offset, io.SEEK_SET)
        return ret

    def fill(self, amount):
        for _ in range(amount):
            self._write(b'\x00')

    def align(self, alignment, base = 0):
        pos = self.tell() - base
        if pos % alignment != 0:
            self.fill(alignment - pos % alignment)

    # ------------ PEEK SECTION ------------ #

    def _peek(self, size=1):
        with self.save_current_pos():
            return self._read(size)

    def peek(self, t):
        size = struct.calcsize(t)
        return struct.unpack(t, self._peek(size))[0]

    def peek_fmt(self, fmt):
        size = struct.calcsize(fmt)
        return struct.unpack(fmt, self._peek(size))

    def peek_uint64(self):
        return self.peek('Q')

    def peek_int64(self):
        return self.peek('q')

    def peek_uint32(self):
        return self.peek('I')

    def peek_int32(self):
        return self.peek('i')

    def peek_uint16(self):
        return self.peek('H')

    def peek_int16(self):
        return self.peek('h')

    def peek_float16(self):
        return self.peek('e')

    def peek_uint8(self):
        return self.peek('B')

    def peek_int8(self):
        return self.peek('b')

    def peek_float(self):
        return self.peek('f')

    def peek_double(self):
        return self.peek('d')

    def peek_fourcc(self):
        with self.save_current_pos():
            return self.read_ascii_string(4)

    # ------------ READ SECTION ------------ #

    def _read(self, size=-1) -> bytes:
        return self.file.read(size)

    def read(self, t):
        size = struct.calcsize(t)
        return struct.unpack(t, self._read(size))[0]

    def read_fmt(self, fmt):
        size = struct.calcsize(fmt)
        return struct.unpack(fmt, self._read(size))

    def read_uint64(self):
        return self.read('Q')

    def read_int64(self):
        return self.read('q')

    def read_uint32(self):
        return self.read('I')

    def read_int32(self):
        return self.read('i')

    def read_uint16(self):
        return self.read('H')

    def read_int16(self):
        return self.read('h')

    def read_uint8(self):
        return self.read('B')

    def read_int8(self):
        return self.read('b')

    def read_float(self):
        return self.read('f')

    def read_double(self):
        return self.read('d')

    def read_ascii_string(self, length=None) ->str:
        if length:
            return bytes(''.join([chr(self.read_uint8()) for _ in range(length)]), 'utf').strip(b'\x00').decode('utf')

        acc = ''
        b = self.read_uint8()
        while b != 0:
            acc += chr(b)
            b = self.read_uint8()
        return acc

    def read_fourcc(self):
        return self.read_ascii_string(4)

    def read_from_offset(self, offset, reader, **reader_args):
        if offset > self.size():
            raise OffsetOutOfBounds()
        # curr_offset = self.tell()
        with self.save_current_pos():
            self.seek(offset, io.SEEK_SET)
            ret = reader(**reader_args)
        # self.seek(curr_offset, io.SEEK_SET)
        return ret

    # ------------ WRITE SECTION ------------ #

    def _write(self, data):
        self.file.write(data)

    def write(self, t, value):
        self._write(struct.pack(t, value))

    def write_fmt(self, fmt, *values):
        self._write(struct.pack(fmt, *values))

    def write_uint64(self, value):
        self.write('Q', value)

    def write_int64(self, value):
        self.write('q', value)

    def write_uint32(self, value):
        self.write('I', value)

    def write_int32(self, value):
        self.write('i', value)

    def write_uint16(self, value):
        self.write('H', value)

    def write_int16(self, value):
        self.write('h', value)

    def write_uint8(self, value):
        self.write('B', value)

    def write_int8(self, value):
        self.write('b', value)

    def write_float(self, value):
        self.write('f', value)

    def write_double(self, value):
        self.write('d', value)

    def write_ascii_string(self, string, zero_terminated=False):
        for c in string:
            self._write(c.encode('ascii'))
        if zero_terminated:
            self._write(b'\x00')

    def write_fourcc(self, fourcc):
        self.write_ascii_string(fourcc)

    def write_to_offset(self, offset, writer, value, fill_to_target=False):
        if offset > self.size() and not fill_to_target:
            raise OffsetOutOfBounds()
        curr_offset = self.tell()
        self.seek(offset, io.SEEK_SET)
        ret = writer(value)
        self.seek(curr_offset, io.SEEK_SET)
        return ret

    def read_bytes(self, size=-1):
        return self._read(size)

    def read_float16(self):
        return self.read('e')

    def write_bytes(self, data):
        self._write(data)

    def read_packed_vector(self):
        num34 = self.read_uint64()
        num35 = num34 & 0xFFFFF
        num34 >>= 20
        num36 = num34 & 1
        num34 >>= 1
        if num36 == 0:
            num35 -= 0x100000
        x = (num35 + 512.5) / 2048
        num35 = num34 & 0xFFFFF
        num34 >>= 20
        num36 = num34 & 1
        num34 >>= 1
        if num36 == 0:
            num35 -= 0x100000
        y = (num35 + 512.5) / 2048
        num35 = num34 & 0xFFFFF
        num34 >>= 20
        num36 = num34 & 1
        num34 >>= 1
        if num36 == 0:
            num35 -= 0x100000
        z = (num35 + 512.5) / 2048
        return x,y,z

    def read_packed_float16(self):
        num35 = self.read_uint16()
        num36 = num35 >> 15
        num35 &= 32767
        if num36 == 0:
            num35 -= 32768
        return num35 / 2048

    def unzip(self):
        return ByteIO(byte_object=zlib.decompress(self.read_bytes()))

if __name__ == '__main__':
    a = ByteIO(path=r'./test.bin', mode='w')
    a.write_fourcc("IDST")
    # a.write_int8(108)
    # a.write_uint32(104)
    # a.write_to_offset(1024,a.write_uint32,84,True)
    # a.write_double(15.58)
    # a.write_float(18.58)
    # a.write_uint64(18564846516)
    # a.write_ascii_string('Test123')
    a.close()
    a = ByteIO(file=open(r'./test.bin', mode='rb'))
    print(a.peek_uint32())
    # print(a.read_from_offset(1024,a.read_uint32))
    # print(a.read_uint32())
    # print(a.read_double())
    # print(a.read_float())
    # print(a.read_uint64())
    # print(a.read_ascii_string())
