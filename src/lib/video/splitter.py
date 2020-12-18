from nmigen import *

from lib.video.image_stream import ImageStream
from util.nmigen_misc import nAny, iterator_with_if_elif


class ImageStreamSplitter(Elaboratable):
    """Splits each image in four sub images. From each 4x4 pixel cluster each image receives one pixel. This can eg. be handy to decompose bayer data."""

    def __init__(self, input: ImageStream, width, height):
        self.input = input

        self.output_top_left = input.clone()
        self.output_top_right = input.clone()
        self.output_bottom_left = input.clone()
        self.output_bottom_right = input.clone()
        self.outputs = [self.output_top_left, self.output_top_right, self.output_bottom_left, self.output_bottom_right]
        self.output_shifts = [(0, 0), (1, 0), (0, 1), (1, 1)]

        self.width = width
        self.height = height

    def elaborate(self, platform):
        m = Module()

        input_transaction = Signal()
        m.d.comb += input_transaction.eq(self.input.ready & self.input.valid)

        x = Signal(16)
        y = Signal(16)
        with m.If(input_transaction):
            with m.If(~self.input.line_last):
                m.d.sync += x.eq(x + 1)
            with m.Else():
                m.d.sync += x.eq(0)
                m.d.sync += y.eq(y + 1)
            with m.If(self.input.frame_last):
                m.d.sync += y.eq(0)

        output_transaction = Signal()
        m.d.comb += output_transaction.eq(nAny(s.ready & s.valid for s in self.outputs))

        for cond, (output, shift) in iterator_with_if_elif(zip(self.outputs, self.output_shifts), m):
            with cond((x % 2 == shift[0]) & (y % 2 == shift[1])):
                m.d.comb += self.input.ready.eq(output.ready)
                m.d.comb += output.valid.eq(self.input.valid)
                m.d.comb += output.payload.eq(self.input.payload)
                # the last signals are used as first signals here and are later converted
                m.d.comb += output.line_last.eq((x // 2) == (self.width - 1) // 2)
                m.d.comb += output.frame_last.eq(((y // 2) == (self.height - 1) // 2) & output.line_last)

        return m
