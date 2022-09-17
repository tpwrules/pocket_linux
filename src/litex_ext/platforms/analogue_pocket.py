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
]

# Platform -----------------------------------------------------------------------------------------

class Platform(AlteraPlatform):
    default_clk_name   = "clk74p25"
    default_clk_period = 1e9/74.25e6

    def __init__(self, toolchain="quartus"):
        AlteraPlatform.__init__(self, "5CEBA4F23C8", _io, toolchain=toolchain)

    def create_programmer(self):
        return USBBlaster()

    def do_finalize(self, fragment):
        AlteraPlatform.do_finalize(self, fragment)
        self.add_period_constraint(self.lookup_request("clk74p25", 0, loose=True), 1e9/74.25e6)
        self.add_period_constraint(self.lookup_request("clk74p25", 1, loose=True), 1e9/74.25e6)
