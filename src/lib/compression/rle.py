from nmigen import *

from lib.bus.stream.stream import PacketizedStream


class ZeroRle(Elaboratable):
    """
    Converts a stream of numbers into a stream of numbers (with identity mapping) and numbers for different
    run lengths of zeroes (with a dict of possible run lengths).
    """
    def __init__(self, input: PacketizedStream, possible_run_lengths_list, zero_value=0, input_max=None):
        self.input = input
        assert possible_run_lengths_list == list(sorted(possible_run_lengths_list))
        self.possible_run_lengths_list = possible_run_lengths_list
        self.max_run_length = max(possible_run_lengths_list)
        self.zero_value = zero_value

        if input_max is None:
            input_max = 2**len(self.input.payload)

        self.output = PacketizedStream(range(input_max + len(possible_run_lengths_list)))

    def elaborate(self, platform):
        m = Module()

        run_length = Signal(range(self.max_run_length))
        with m.FSM():
            with m.State("NONZERO"):
                with m.If(((self.input.payload != self.zero_value) | self.input.last) & self.input.valid):
                    m.d.comb += self.output.connect_upstream(self.input)
                    m.d.sync += run_length.eq(0)
                with m.Elif(self.input.valid):
                    m.next = "ZERO_COUNT"
                    m.d.comb += self.input.ready.eq(1)
                    m.d.sync += run_length.eq(1)

            run_length_index = Signal(range(len(self.possible_run_lengths_list)))
            run_length_array = Array([1, *self.possible_run_lengths_list])

            with m.State("ZERO_COUNT"):
                with m.If(((self.input.payload != self.zero_value) | self.input.last) & self.input.valid):
                    m.next = "ZERO_OUT"
                    m.d.sync += run_length_index.eq(len(self.possible_run_lengths_list))
                with m.Elif(self.input.valid & (run_length < self.max_run_length - 1)):
                    m.d.comb += self.input.ready.eq(1)
                    m.d.sync += run_length.eq(run_length + 1)
                with m.Elif(self.input.valid):
                    m.d.comb += self.input.ready.eq(1)
                    m.d.sync += run_length.eq(run_length + 1)
                    m.next = "ZERO_OUT"
                    m.d.sync += run_length_index.eq(len(self.possible_run_lengths_list))

            with m.State("ZERO_OUT"):
                with m.If(run_length == 0):
                    m.next = "NONZERO"
                with m.Elif((run_length_array[run_length_index] <= run_length) & self.output.ready):
                    with m.If(run_length_index == 0):
                        m.d.comb += self.output.payload.eq(self.zero_value)
                    with m.Else():
                        m.d.comb += self.output.payload.eq((2**len(self.input.payload)) + run_length_index - 1)
                    m.d.comb += self.output.valid.eq(1)
                    m.d.sync += run_length.eq(run_length - run_length_array[run_length_index])
                with m.Elif(self.output.ready):
                    m.d.sync += run_length_index.eq(run_length_index - 1)

        return m
