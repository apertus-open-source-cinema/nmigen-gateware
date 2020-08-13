from nmigen.build import *
from nmigen.vendor.lattice_machxo_2_3l import *

__all__ = ["Usb3PluginPlatform"]


class Usb3PluginPlatform(LatticeMachXO2Platform):
    device = "LCMXO2-1200HC"
    package = "TG100"
    speed = "6"

    resources = [
        Resource("ft601", 0,
            Subsignal("reset", PinsN("4", dir="o"), Attrs(IO_TYPE="LVCMOS33")),

            Subsignal("data", Pins("75 74 70 69 68 67 66 65 64 61 60 59 58 57 54 53 83 84 85 86 87 88 96 97 98 99 7 8 21 24 20 25", dir="io"), Attrs(IO_TYPE="LVCMOS33")),
            Subsignal("be", Pins("19 18 17 16", dir="io"), Attrs(IO_TYPE="LVCMOS33")),
            Subsignal("oe", PinsN("9", dir="o"), Attrs(IO_TYPE="LVCMOS33")),

            Subsignal("read", PinsN("10", dir="o"), Attrs(IO_TYPE="LVCMOS33")),
            Subsignal("write", PinsN("12", dir="o"), Attrs(IO_TYPE="LVCMOS33")),
            Subsignal("siwu", PinsN("13", dir="o"), Attrs(IO_TYPE="LVCMOS33")),
            Subsignal("rxf", PinsN("14", dir="i"), Attrs(IO_TYPE="LVCMOS33")),
            Subsignal("txe", PinsN("15", dir="i"), Attrs(IO_TYPE="LVCMOS33")),

            Subsignal("gpio", Pins("2 1", dir="io"), Attrs(IO_TYPE="LVCMOS33")),
            Subsignal("wakeup", PinsN("3", dir="io"), Attrs(IO_TYPE="LVCMOS33")),

            Subsignal("clk", Pins("63", dir="i"), Attrs(IO_TYPE="LVCMOS33"), Clock(100e6)),
            Subsignal("clk1", Pins("62", dir="i"), Attrs(IO_TYPE="LVCMOS33"), Clock(100e6)),

            ),

        Resource("led", 0, Pins("71", dir="o"), Attrs(IO_TYPE="LVCMOS33")),

        Resource("plugin_stream_input", 0,
            Subsignal("lvds0", DiffPairs("45", "47", dir="i"), Attrs(IO_TYPE="LVDS25")),
            Subsignal("lvds1", DiffPairs("42", "43", dir="i"), Attrs(IO_TYPE="LVDS25")),
            Subsignal("lvds2", DiffPairs("40", "41", dir="i"), Attrs(IO_TYPE="LVDS25")),
            Subsignal("lvds3", DiffPairs("36", "37", dir="i"), Attrs(IO_TYPE="LVDS25")),
            Subsignal("clk_word", DiffPairs("34", "35", dir="i"), Attrs(IO_TYPE="LVDS25"), Clock(100e6)),  # lvds4
            Subsignal("valid", DiffPairs("29", "30", dir="i"), Attrs(IO_TYPE="LVDS25")),  # lvds5
        )
    ]
    connectors = []
