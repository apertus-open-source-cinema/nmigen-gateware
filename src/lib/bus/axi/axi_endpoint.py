import math
from enum import Enum

from nmigen import *

from lib.bus.stream.stream import BasicStream, Stream
from lib.data_structure.bundle import Bundle, UPWARDS, DOWNWARDS
from lib.data_structure.packed_struct import packed_struct


class Response(Enum):
    OKAY = 0b00
    EXOKAY = 0b01
    SLVERR = 0b10
    DECERR = 0b11


class BurstType(Enum):
    FIXED = 0b00
    INCR = 0b01
    WRAP = 0b10


@packed_struct
class ProtectionType:
    privileged: unsigned(1)
    secure: unsigned(1)
    is_instruction: unsigned(1)


class AddressStream(BasicStream):
    def __init__(self, addr_bits, lite, id_bits, data_bytes, src_loc_at=1):
        assert addr_bits % 8 == 0
        super().__init__(addr_bits, src_loc_at=1 + src_loc_at)
        if not lite:
            self.id = Signal(id_bits)
            self.burst_type = Signal(BurstType)
            self.burst_len = Signal(range(16))  # in axi3 a burst can have a length of 16 as a hardcoded maximum
            self.beat_size_bytes = Signal(3, reset=int(math.log2(data_bytes)))  # this is 2**n encoded
            self.protection_type = Signal(ProtectionType().as_value().shape())


class DataStream(BasicStream):
    def __init__(self, data_bits, read, lite, id_bits, src_loc_at=1, **kwargs):
        assert data_bits % 8 == 0
        super().__init__(data_bits, src_loc_at=1 + src_loc_at, **kwargs)
        if read:
            self.resp = Signal(Response)
        else:
            self.byte_strobe = Signal(data_bits // 8)

        if not lite:
            self.last = Signal()
            self.id = Signal(id_bits)


class WriteResponseStream(Stream):
    def __init__(self, lite, id_bits, src_loc_at=1, **kwargs):
        super().__init__(src_loc_at=1 + src_loc_at, **kwargs)

        self.ready = Signal() @ UPWARDS
        self.valid = Signal()
        self.resp = Signal(Response)

        if not lite:
            self.id = Signal(id_bits)


class AxiEndpoint(Bundle):
    @staticmethod
    def like(model, lite=None, name="axi", **kwargs):
        """
        Create an AxiInterface shaped like a given model.
        :param name: the name of the resulting axi port
        :type model: AxiEndpoint
        :param model: the model after which the axi port should be created
        :param lite: overrides the lite property of the model. Only works for creating an AXI lite inteface from an AXI full bus.
        :return:
        """
        if lite is False:
            assert not model.is_lite, "cant make up id_bits out of thin air"

        return AxiEndpoint(
            addr_bits=model.addr_bits,
            data_bits=model.data_bits,
            lite=lite if lite is not None else model.is_lite,
            id_bits=None if (lite is not None and lite) else model.id_bits,
            name=name,
            **kwargs
        )

    def __init__(self, *, addr_bits, data_bits, lite, id_bits=None, src_loc_at=1, **kwargs):
        """
        Constructs a Record holding all the signals for axi (lite)

        :param addr_bits: the number of bits the address signal has.
        :param data_bits: the number of bits the
        :param lite: whether to construct an AXI lite or full bus.
        :param id_bits: the number of bits for the id signal of full axi. do not specify if :param lite is True.
        """
        super().__init__(**kwargs, src_loc_at=1 + src_loc_at)

        if id_bits:
            assert not lite, "there is no id tracking on axi lite buses"
        if lite:
            assert id_bits is None
        self.addr_bits = addr_bits
        self.data_bits = data_bits
        self.data_bytes = data_bits // 8
        assert math.log2(self.data_bytes) == int(math.log2(self.data_bytes))
        self.is_lite = lite
        self.id_bits = id_bits

        lite_args = {"lite": lite, "id_bits": id_bits}
        self.read_address = AddressStream(addr_bits, data_bytes=self.data_bytes, **lite_args) @ DOWNWARDS
        self.read_data = DataStream(data_bits, read=True, **lite_args) @ UPWARDS

        self.write_address = AddressStream(addr_bits, data_bytes=self.data_bytes, **lite_args) @ DOWNWARDS
        self.write_data = DataStream(data_bits, read=False, **lite_args) @ DOWNWARDS
        self.write_response = WriteResponseStream(**lite_args) @ UPWARDS
