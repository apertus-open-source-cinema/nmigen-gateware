import unittest

from lib.bus.stream.gearbox import StreamGearbox
from lib.bus.stream.sim_util import read_from_stream, write_to_stream
from lib.bus.stream.stream import BasicStream, PacketizedStream
from util.sim import SimPlatform, do_nothing


class TestGearbox(unittest.TestCase):
    def test_gearbox_7_to_3(self):
        input = BasicStream(7)
        dut = StreamGearbox(input, 3)

        def writer():
            yield from write_to_stream(input, payload=0b0_010_001)
            yield from write_to_stream(input, payload=0b10_011_10)
            yield from write_to_stream(input, payload=0b000_111_1)

        def reader():
            self.assertEqual((yield from read_from_stream(dut.output)), 0b001)
            self.assertEqual((yield from read_from_stream(dut.output)), 0b010)
            self.assertEqual((yield from read_from_stream(dut.output)), 0b100)
            self.assertEqual((yield from read_from_stream(dut.output)), 0b011)
            self.assertEqual((yield from read_from_stream(dut.output)), 0b110)
            self.assertEqual((yield from read_from_stream(dut.output)), 0b111)
            self.assertEqual((yield from read_from_stream(dut.output)), 0b000)

        platform = SimPlatform()
        platform.add_sim_clock("sync", 100e6)
        platform.add_process(writer, "sync")
        platform.add_process(reader, "sync")
        platform.sim(dut)

    def test_gearbox_3_to_7(self):
        input = BasicStream(3)
        dut = StreamGearbox(input, 7)

        def writer():
            yield from write_to_stream(input, payload=0b001)
            yield from write_to_stream(input, payload=0b010)
            yield from write_to_stream(input, payload=0b100)
            yield from write_to_stream(input, payload=0b011)
            yield from write_to_stream(input, payload=0b110)
            yield from write_to_stream(input, payload=0b111)
            yield from write_to_stream(input, payload=0b000)

        def reader():
            self.assertEqual((yield from read_from_stream(dut.output)), 0b0_010_001)
            self.assertEqual((yield from read_from_stream(dut.output)), 0b10_011_10)
            self.assertEqual((yield from read_from_stream(dut.output)), 0b000_111_1)

        platform = SimPlatform()
        platform.add_sim_clock("sync", 100e6)
        platform.add_process(writer, "sync")
        platform.add_process(reader, "sync")
        platform.sim(dut)

    def test_gearbox_4_to_8_last(self):
        input = PacketizedStream(4)
        dut = StreamGearbox(input, 8)

        def writer():
            yield from write_to_stream(input, payload=0b0001, last=0)
            yield from write_to_stream(input, payload=0b0010, last=1)
            yield from write_to_stream(input, payload=0b0100, last=0)
            yield from write_to_stream(input, payload=0b1000, last=0)

        def reader():
            self.assertEqual((yield from read_from_stream(dut.output, extract=("payload", "last"))), (0b0010_0001, 1))
            self.assertEqual((yield from read_from_stream(dut.output, extract=("payload", "last"))), (0b1000_0100, 0))

        platform = SimPlatform()
        platform.add_sim_clock("sync", 100e6)
        platform.add_process(writer, "sync")
        platform.add_process(reader, "sync")
        platform.sim(dut)

    def test_gearbox_8_to_4_last(self):
        input = PacketizedStream(8)
        dut = StreamGearbox(input, 4)

        def writer():
            yield from write_to_stream(input, payload=0b00_10_00_01, last=1)
            yield from write_to_stream(input, payload=0b10_00_01_00, last=0)

        def reader():
            self.assertEqual((yield from read_from_stream(dut.output, extract=("payload", "last"))), (0b0001, 0))
            self.assertEqual((yield from read_from_stream(dut.output, extract=("payload", "last"))), (0b0010, 1))
            self.assertEqual((yield from read_from_stream(dut.output, extract=("payload", "last"))), (0b0100, 0))
            self.assertEqual((yield from read_from_stream(dut.output, extract=("payload", "last"))), (0b1000, 0))

        platform = SimPlatform()
        platform.add_sim_clock("sync", 100e6)
        platform.add_process(writer, "sync")
        platform.add_process(reader, "sync")
        platform.sim(dut)

    def test_dont_loose_data(self):
        input = BasicStream(16)
        dut = StreamGearbox(input, 8)

        def writer():
            for i in range(0, 100, 2):
                print("{:016b}".format(((i + 1) << 8) | i))
                yield from write_to_stream(input, payload=(((i + 1) << 8) | i))
                if i % 3 == 0:
                    yield from do_nothing()

        def reader():
            for i in range(100):
                got = (yield from read_from_stream(dut.output, extract="payload"))
                print(got)
                self.assertEqual(got, i)
                if i % 10 == 0:
                    yield from do_nothing()

        platform = SimPlatform()
        platform.add_sim_clock("sync", 100e6)
        platform.add_process(writer, "sync")
        platform.add_process(reader, "sync")
        platform.sim(dut)

    def test_dont_loose_last_8_to_4(self):
        input = PacketizedStream(8)
        dut = StreamGearbox(input, 4)

        def writer():
            last_count_gold = 0
            for i in range(50):
                last = (i % 5 == 0)
                last_count_gold += last
                yield from write_to_stream(input, payload=0, last=(i % 5 == 0))
                if i % 3 == 0:
                    yield from do_nothing()
            self.assertEqual(last_count_gold, 10)

        def reader():
            last_count = 0
            for i in range(100):
                last_count += (yield from read_from_stream(dut.output, extract="last"))
                if i % 10 == 0:
                    yield from do_nothing()
            self.assertEquals(last_count, 10)

        platform = SimPlatform()
        platform.add_sim_clock("sync", 100e6)
        platform.add_process(writer, "sync")
        platform.add_process(reader, "sync")
        platform.sim(dut)

    def test_dont_loose_last_16_to_4(self):
        input = PacketizedStream(16)
        dut = StreamGearbox(input, 4)

        def writer():
            last_count_gold = 0
            for i in range(50):
                last = (i % 5 == 0)
                last_count_gold += last
                yield from write_to_stream(input, payload=0, last=(i % 5 == 0))
                if i % 3 == 0:
                    yield from do_nothing()
            self.assertEqual(last_count_gold, 10)

        def reader():
            last_count = 0
            for i in range(200):
                last_count += (yield from read_from_stream(dut.output, extract="last"))
                if i % 10 == 0:
                    yield from do_nothing()
            self.assertEquals(last_count, 10)

        platform = SimPlatform()
        platform.add_sim_clock("sync", 100e6)
        platform.add_process(writer, "sync")
        platform.add_process(reader, "sync")
        platform.sim(dut)