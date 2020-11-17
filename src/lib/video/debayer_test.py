import unittest
from os.path import join, dirname

from nmigen import *
from nmigen.sim import Passive

from lib.bus.stream.sim_util import write_to_stream
from lib.video.debayer import RecoloringDebayerer, SimpleInterpolatingDebayerer
from lib.video.image_stream import ImageStream
from lib.video.test_util import write_frame_to_stream, read_frame_from_stream, to_8bit_rgb
from util.sim import SimPlatform
import imageio


class DebayerTest(unittest.TestCase):
    def check_output_stable(self, debayerer_gen):
        platform = SimPlatform()
        m = Module()

        input = ImageStream(8)
        transformer = m.submodules.transformer = debayerer_gen(input)
        image = imageio.imread(join(dirname(__file__), "test_bayer.png"))

        def write_process():
            yield from write_frame_to_stream(input, image, pause=False)
            yield from write_frame_to_stream(input, image, pause=False)
            yield from write_frame_to_stream(input, image, pause=False)
            yield Passive()
            while True:
                yield from write_to_stream(input, line_last=0, frame_last=0, payload=0)

        def read_process():
            (yield from read_frame_from_stream(transformer.output, timeout=1000, pause=False))
            first = to_8bit_rgb((yield from read_frame_from_stream(transformer.output, timeout=1000, pause=False)))
            second = to_8bit_rgb((yield from read_frame_from_stream(transformer.output, timeout=1000, pause=False)))
            imageio.imsave(platform.output_filename_base + "_first.png", first)
            imageio.imsave(platform.output_filename_base + "_second.png", second)
            self.assertEqual(first, second)

        platform.add_sim_clock("sync", 100e6)
        platform.add_process(write_process, "sync")
        platform.sim(m, read_process)

    def test_output_stable_recoloring_debayerer(self):
        self.check_output_stable(RecoloringDebayerer)

    def test_output_stable_simple_interpolating_debayerer(self):
        self.check_output_stable(lambda input: SimpleInterpolatingDebayerer(input, 70, 48))