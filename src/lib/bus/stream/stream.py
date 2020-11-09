from nmigen import *

from lib.data_structure.bundle import Bundle, UPWARDS, DOWNWARDS


class Stream(Bundle):
    """
    A stream is everything that inherits from `Bundle` and has a ready@UPWARDS, a valid@DOWNWARDS.
    Stream Sinks (downstream) pull ready high if they can accept data and stream Sources (upstream) pull valid
    high if they have data to offer. Both ready-before-valid and valid-before-ready are allowed.
    A successful data transfer on the stream happens if ready and valid are 1 during a cycle.

    Optionally Streams may have any number of DOWNWARDS Signals, that carry actual payload and/or out-of-band signaling
    (e.g. last or first) as their payload.

    Streams have to implement a clone() methods that returns a Stream that is shaped just like the original stream
    but not connected to it.

    This is the base Stream class that is pretty much useless on its own. Other Classes are implementing Streams that
    are useful for real use-cases. Probably you are looking for `BasicStream`
    """

    def __init__(self, name=None, src_loc_at=1):
        super().__init__(name=name, src_loc_at=1 + src_loc_at)

        self.ready = Signal() @ UPWARDS
        self.valid = Signal() @ DOWNWARDS

    def clone(self, name=None):
        return self.__class__(name=name)

    @property
    def payload_signals(self):
        return {k: getattr(self, k) for k in self._downwards_ports if k != "valid"}


class BasicStream(Stream):
    """A basic stream that carries a payload"""

    def __init__(self, payload_shape, name=None, src_loc_at=1):
        super().__init__(name=name, src_loc_at=1 + src_loc_at)
        self.payload = Signal(payload_shape) @ DOWNWARDS

    def clone(self, name=None):
        return self.__class__(self.payload.shape(), name=name)

    @property
    def out_of_band_signals(self):
        return {k: v for k, v in self.payload_signals.items() if k != "payload"}


class PacketizedStream(BasicStream):
    """
    A stream that carries a payload and can separate Packets via a last signal that is asserted on the
    last word of a packet
    """

    def __init__(self, payload_shape, name=None, src_loc_at=1):
        super().__init__(payload_shape, name, src_loc_at=1 + src_loc_at)
        self.last = Signal() @ DOWNWARDS
