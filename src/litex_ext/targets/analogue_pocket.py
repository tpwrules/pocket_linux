#!/usr/bin/env python3

#
# This file is part of LiteX-Boards.
#
# Copyright (c) 2020 Paul Sajna <sajattack@gmail.com>
# Copyright (c) 2022 Thomas Watson <twatson52@icloud.com>
# SPDX-License-Identifier: BSD-2-Clause

from migen import *

from litex.build.io import DDROutput

from litex_ext.platforms import analogue_pocket

from litex.soc.cores.clock import CycloneVPLL
from litex.soc.integration.soc import SoCRegion
from litex.soc.integration.soc_core import *
from litex.soc.integration.builder import *

from litedram.modules import AS4C32M16
from litedram.phy import GENSDRPHY, HalfRateGENSDRPHY

# CRG ----------------------------------------------------------------------------------------------

class _CRG(Module):
    def __init__(self, platform, sys_clk_freq, sdram_rate="1:1"):
        self.rst = Signal()
        self.clock_domains.cd_sys    = ClockDomain()
        if sdram_rate == "1:2":
            self.clock_domains.cd_sys2x    = ClockDomain()
            self.clock_domains.cd_sys2x_ps = ClockDomain()
        else:
            self.clock_domains.cd_sys_ps = ClockDomain()

        # # #

        # Clk / Rst
        clk74p25 = platform.request("clk74p25")

        # PLL
        self.submodules.pll = pll = CycloneVPLL(speedgrade="-C8")
        self.comb += pll.reset.eq(self.rst)
        pll.register_clkin(clk74p25, 74.25e6)
        pll.create_clkout(self.cd_sys,    sys_clk_freq)
        if sdram_rate == "1:2":
            pll.create_clkout(self.cd_sys2x,    2*sys_clk_freq)
            # allegedly the phase should be 90 degrees but the ram doesn't work
            # unless set to 180
            pll.create_clkout(self.cd_sys2x_ps, 2*sys_clk_freq, phase=180)
        else:
            pll.create_clkout(self.cd_sys_ps, sys_clk_freq, phase=90)

        sdram_clk = ClockSignal("sys2x_ps" if sdram_rate == "1:2" else "sys_ps")
        self.specials += DDROutput(1, 0, platform.request("sdram_clock"), sdram_clk)

# BaseSoC ------------------------------------------------------------------------------------------

class BaseSoC(SoCCore):
    def __init__(self, sys_clk_freq=int(50e6), sdram_rate="1:1", **kwargs):
        platform = analogue_pocket.Platform()

        # CRG --------------------------------------------------------------------------------------
        self.submodules.crg = _CRG(platform, sys_clk_freq, sdram_rate=sdram_rate)

        # SoCCore ----------------------------------------------------------------------------------
        # Defaults to JTAG-UART since no hardware UART.
        real_uart_name = kwargs["uart_name"]
        if real_uart_name == "serial":
            kwargs["uart_name"] = "jtag_uart"
        SoCCore.__init__(self, platform, sys_clk_freq, ident="LiteX SoC on Analogue Pocket", **kwargs)

        # SDR SDRAM --------------------------------------------------------------------------------
        sdrphy_cls = HalfRateGENSDRPHY if sdram_rate == "1:2" else GENSDRPHY
        self.submodules.sdrphy = sdrphy_cls(platform.request("sdram"), sys_clk_freq)
        self.add_sdram("sdram",
            phy           = self.sdrphy,
            module        = AS4C32M16(sys_clk_freq, sdram_rate),
            l2_cache_size = kwargs.get("l2_size", 8192)
        )

# Build --------------------------------------------------------------------------------------------

def main():
    from litex.soc.integration.soc import LiteXSoCArgumentParser
    parser = LiteXSoCArgumentParser(description="LiteX SoC on Analogue Pocket")
    target_group = parser.add_argument_group(title="Target options")
    target_group.add_argument("--build",                      action="store_true", help="Build design.")
    target_group.add_argument("--load",                       action="store_true", help="Load bitstream.")
    target_group.add_argument("--sys-clk-freq",               default=50e6,        help="System clock frequency.")
    target_group.add_argument("--sdram-rate",                 default="1:1",       help="SDRAM Rate (1:1 Full Rate or 1:2 Half Rate).")
    builder_args(parser)
    soc_core_args(parser)
    args = parser.parse_args()

    soc = BaseSoC(
        sys_clk_freq               = int(float(args.sys_clk_freq)),
        sdram_rate                 = args.sdram_rate,
        **soc_core_argdict(args)
    )
    builder = Builder(soc, **builder_argdict(args))
    if args.build:
        builder.build()

    if args.load:
        prog = soc.platform.create_programmer()
        prog.load_bitstream(builder.get_bitstream_filename(mode="sram"))

if __name__ == "__main__":
    main()
