# a helper for interfacing the ft601 usb3 fifo bridge in 245 Synchronous FIFO mode

from nmigen import *

from lib.bus.stream.fifo import BufferedAsyncStreamFIFO, BufferedSyncStreamFIFO
from lib.bus.stream.stream import Stream


class FT601StreamSinkNoCDC(Elaboratable):
    def __init__(self, ft601_resource, input: Stream, save_to_begin_new_transaction=None):
        self.ft_601_resource = ft601_resource
        assert len(input.payload) == 32
        self.input = input
        self.safe_to_begin_new_transaction = save_to_begin_new_transaction

    def elaborate(self, platform):
        m = Module()

        ft = self.ft_601_resource

        m.d.comb += ft.be.oe.eq(1)
        m.d.comb += ft.be.o.eq(0b1111)  # everything we write is valid

        m.d.comb += ft.oe.eq(0)  # we are driving the data bits all the time
        m.d.comb += ft.data.oe.eq(1)

        if self.safe_to_begin_new_transaction is None:
            m.d.comb += ft.data.o.eq(self.input.payload)
            m.d.comb += self.input.ready.eq(ft.txe)
            m.d.comb += ft.write.eq(self.input.valid)
        else:
            in_transaction = Signal()
            m.d.sync += in_transaction.eq(ft.write)
            with m.If(in_transaction):
                m.d.comb += ft.write.eq(self.input.valid & ft.txe)
                m.d.comb += self.input.ready.eq(ft.txe)
            with m.Else():
                m.d.comb += self.input.ready.eq(ft.txe & self.safe_to_begin_new_transaction)
                m.d.comb += ft.write.eq(self.input.valid & self.safe_to_begin_new_transaction)
            m.d.comb += ft.data.o.eq(self.input.payload)
        m.d.comb += platform.request("led", 0).eq(ft.txe)

        return m


class FT601StreamSink(Elaboratable):
    def __init__(self, ft601_resource, input_stream, async_fifo_depth=128, begin_transactions_at_level=2040):
        self.ft601_resource = ft601_resource
        self.input_stream = input_stream
        self.async_fifo_depth = async_fifo_depth
        self.begin_transactions_at_level = begin_transactions_at_level

    def elaborate(self, platform):
        m = Module()

        m.domains += ClockDomain("ft601")
        m.d.comb += ClockSignal("ft601").eq(self.ft601_resource.clk)

        # we use two fifos here as a performance optimization because (i guess) large async fifos are bad for fmax
        # TODO: verify hypothesis
        cdc_fifo = m.submodules.cdc_fifo = BufferedAsyncStreamFIFO(self.input_stream, self.async_fifo_depth, i_domain="sync", o_domain="ft601")
        buffer_fifo_depth = (self.begin_transactions_at_level + 2 - self.async_fifo_depth)
        buffer_fifo = m.submodules.buffer_fifo = DomainRenamer("ft601")(BufferedSyncStreamFIFO(cdc_fifo.output, buffer_fifo_depth))
        save_to_begin_new_transaction = Signal()
        m.d.comb += save_to_begin_new_transaction.eq((buffer_fifo.r_level + cdc_fifo.r_level) >= self.begin_transactions_at_level)
        m.submodules.ft601 = DomainRenamer("ft601")(FT601StreamSinkNoCDC(
            self.ft601_resource,
            buffer_fifo.output,
            save_to_begin_new_transaction,
        ))

        return m