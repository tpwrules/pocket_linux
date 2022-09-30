#
# This file is part of LiteX-Boards.
#
# Copyright (c) 2020 Paul Sajna <sajattack@gmail.com>
# Copyright (c) 2022 Thomas Watson <twatson52@icloud.com>
# SPDX-License-Identifier: BSD-2-Clause

from litex.build.generic_platform import *
from litex.build.altera import AlteraPlatform
from litex.build.altera.programmer import USBBlaster

# IOs ----------------------------------------------------------------------------------------------

_io = [
    # Clk / Rst
    ("clk74p25", 0, Pins("V15"), IOStandard("3.3-V LVCMOS")),
    ("clk74p25", 1, Pins("H16"), IOStandard("1.8 V")),

    # SDR SDRAM
    ("sdram_clock", 0, Pins("G12"), IOStandard("1.8 V"),
        Misc("OUTPUT_TERMINATION \"SERIES 50 OHM WITHOUT CALIBRATION\"")),
    ("sdram", 0,
        Subsignal("cke", Pins("G18")),
        Subsignal("a",   Pins(
            "D17 D12 F12 E14 F13 E16 E15 F14",
            "J18 G17 C13 F15 J17")),
        Subsignal("dq",  Pins(
            "C15 B15 A15 B13 A14 B12 A13 A12",
            "J13 G15 G16 G13 H13 J19 G11 K20"),
            ),
        Subsignal("dm", Pins("D13 H18")),
        Subsignal("ba",    Pins("C16 E12")),
        Subsignal("cas_n", Pins("B16")),
        Subsignal("ras_n", Pins("B11")),
        Subsignal("we_n",  Pins("C11")),
        Misc("CURRENT_STRENGTH_NEW \"4MA\""),
        IOStandard("1.8 V"),
    ),

    # scaler video connection
    ("vid", 0,
        Subsignal("clk", Pins("R17")),
        Subsignal("de", Pins("N20")),
        Subsignal("skip", Pins("N21")),
        Subsignal("hsync", Pins("P17")),
        Subsignal("vsync", Pins("T15")),
        Subsignal("data", Pins(
            "R21 P22 N16 P18 P19 T20 T19 T18 T22 R22 R15 R16"
        )),
        Misc("OUTPUT_TERMINATION \"SERIES 50 OHM WITHOUT CALIBRATION\""),
        IOStandard("1.8 V"),
    ),
]

# Platform -----------------------------------------------------------------------------------------

class Platform(AlteraPlatform):
    default_clk_name   = "clk74p25"
    default_clk_period = 1e9/74.25e6

    def __init__(self, toolchain="quartus"):
        AlteraPlatform.__init__(self, "5CEBA4F23C8", _io, toolchain=toolchain)
        self.toolchain.additional_sdc_commands.extend([
            f"create_clock -period {1e9/6e6:.3f} [get_ports {{altera_reserved_tck}}]",
            "set_clock_groups -asynchronous -group {altera_reserved_tck}"
        ])

    def create_programmer(self):
        return USBBlaster()

    def do_finalize(self, fragment):
        AlteraPlatform.do_finalize(self, fragment)
        self.add_period_constraint(self.lookup_request("clk74p25", 0, loose=True), 1e9/74.25e6)
        self.add_period_constraint(self.lookup_request("clk74p25", 1, loose=True), 1e9/74.25e6)
