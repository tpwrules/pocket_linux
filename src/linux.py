#!/usr/bin/env python3

#
# This file is part of Linux-on-LiteX-VexRiscv
#
# Copyright (c) 2019-2022, Linux-on-LiteX-VexRiscv Developers
# SPDX-License-Identifier: BSD-2-Clause

import os
import sys
import argparse
import json
import shutil
import subprocess

from migen import *

from litex.soc.interconnect.csr import *

from litex.soc.integration.builder import Builder
from litex.soc.cores.cpu.vexriscv_smp import VexRiscvSMP

from litex.tools.litex_json2dts_linux import generate_dts

# SoCLinux -----------------------------------------------------------------------------------------

def SoCLinux(soc_cls, **kwargs):
    class _SoCLinux(soc_cls):
        def __init__(self, **kwargs):

            # SoC ----------------------------------------------------------------------------------
            soc_cls.__init__(self,
                cpu_type       = "vexriscv_smp",
                cpu_variant    = "linux",
                **kwargs)

        # DTS generation ---------------------------------------------------------------------------
        def generate_dts(self, board_name):
            json_src = os.path.join("build", board_name, "csr.json")
            dts = os.path.join("build", board_name, "{}.dts".format(board_name))

            with open(json_src) as json_file, open(dts, "w") as dts_file:
                dts_content = generate_dts(json.load(json_file), polling=False)
                dts_file.write(dts_content)

        # DTS compilation --------------------------------------------------------------------------
        def compile_dts(self, board_name, symbols=False):
            dts = os.path.join("build", board_name, "{}.dts".format(board_name))
            dtb = os.path.join("build", board_name, "{}.dtb".format(board_name))
            subprocess.check_call(
                "dtc {} -O dtb -o {} {}".format("-@" if symbols else "", dtb, dts), shell=True)

        # DTB combination --------------------------------------------------------------------------
        def combine_dtb(self, board_name, overlays=""):
            dtb_in = os.path.join("build", board_name, "{}.dtb".format(board_name))
            dtb_out = os.path.join("images", "rv32.dtb")
            if overlays == "":
                shutil.copyfile(dtb_in, dtb_out)
            else:
                subprocess.check_call(
                    "fdtoverlay -i {} -o {} {}".format(dtb_in, dtb_out, overlays), shell=True)

        # Documentation generation -----------------------------------------------------------------
        def generate_doc(self, board_name):
            from litex.soc.doc import generate_docs
            doc_dir = os.path.join("build", board_name, "doc")
            generate_docs(self, doc_dir)
            os.system("sphinx-build -M html {}/ {}/_build".format(doc_dir, doc_dir))

    return _SoCLinux(**kwargs)


# Board Definition ---------------------------------------------------------------------------------

class Board:
    soc_kwargs = {
        "integrated_rom_size"  : 0x10000,
        "integrated_sram_size" : 0x1800,
        "l2_size"              : 0,
    }
    def __init__(self, soc_cls=None, soc_capabilities={}, soc_constants={}):
        self.soc_cls          = soc_cls
        self.soc_capabilities = soc_capabilities
        self.soc_constants    = soc_constants

    def load(self, filename):
        prog = self.platform.create_programmer()
        prog.load_bitstream(filename)

    def flash(self, filename):
        prog = self.platform.create_programmer()
        prog.flash(0, filename)

#---------------------------------------------------------------------------------------------------
# Intel Boards
#---------------------------------------------------------------------------------------------------

# Analogue Pocket support --------------------------------------------------------------------------

class Pocket(Board):
    soc_kwargs = {
        "l2_size"           : 2048, # Use Wishbone and L2 for memory accesses.
        "integrated_rom_size": 0x7000,
        "integrated_sram_size": 0xb00,
        "uart_name"         : "jtag_uart",
        # optimal speed to make the jtag uart downloading work properly...
        "sys_clk_freq"      : 70e6,
        # for reproducibility
        "no_ident_version"  : True,
    }
    def __init__(self):
        from litex_ext.targets import analogue_pocket
        Board.__init__(self, analogue_pocket.BaseSoC, soc_capabilities={
            # Communication
            "serial",
        })


supported_boards = {
    # Altera/Intel
    "pocket"                      : Pocket,
    }

def main():
    description = "Linux on LiteX-VexRiscv\n\n"
    description += "Available boards:\n"
    for name in sorted(supported_boards.keys()):
        description += "- " + name + "\n"
    parser = argparse.ArgumentParser(description=description, formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("--board",          default="pocket",            help="FPGA board.")
    parser.add_argument("--build",          action="store_true",         help="Build bitstream.")
    parser.add_argument("--load",           action="store_true",         help="Load bitstream (to SRAM).")
    parser.add_argument("--flash",          action="store_true",         help="Flash bitstream/images (to Flash).")
    parser.add_argument("--doc",            action="store_true",         help="Build documentation.")
    parser.add_argument("--fdtoverlays",    default="",                  help="Device Tree Overlays to apply.")
    VexRiscvSMP.args_fill(parser)
    args = parser.parse_args()

    # Board(s) selection ---------------------------------------------------------------------------
    if args.board == "all":
        board_names = list(supported_boards.keys())
    else:
        args.board = args.board.lower()
        args.board = args.board.replace(" ", "_")
        board_names = [args.board]

    # Board(s) iteration ---------------------------------------------------------------------------
    for board_name in board_names:
        board = supported_boards[board_name]()
        soc_kwargs = Board.soc_kwargs
        soc_kwargs.update(board.soc_kwargs)

        # CPU parameters ---------------------------------------------------------------------------

        # If Wishbone Memory is forced, enabled L2 Cache (if not already):
        if args.with_wishbone_memory:
            soc_kwargs["l2_size"] = max(soc_kwargs["l2_size"], 2048) # Defaults to 2048.
        # Else if board is configured to use L2 Cache, force use of Wishbone Memory on VexRiscv-SMP.
        else:
            args.with_wishbone_memory = soc_kwargs["l2_size"] != 0

        VexRiscvSMP.args_read(args)

        # SoC creation -----------------------------------------------------------------------------
        soc = SoCLinux(board.soc_cls, **soc_kwargs)
        board.platform = soc.platform

        # SoC constants ----------------------------------------------------------------------------
        for k, v in board.soc_constants.items():
            soc.add_constant(k, v)

        # Build ------------------------------------------------------------------------------------
        build_dir = os.path.join("build", board_name)
        builder   = Builder(soc,
            output_dir   = os.path.join("build", board_name),
            # bios_console = "lite",
            csr_json     = os.path.join(build_dir, "csr.json"),
            csr_csv      = os.path.join(build_dir, "csr.csv")
        )
        builder.build(run=args.build, build_name=board_name)

        # DTS --------------------------------------------------------------------------------------
        soc.generate_dts(board_name)
        soc.compile_dts(board_name, args.fdtoverlays)

        # DTB --------------------------------------------------------------------------------------
        soc.combine_dtb(board_name, args.fdtoverlays)

        # PCIe Driver ------------------------------------------------------------------------------
        if "pcie" in board.soc_capabilities:
            from litepcie.software import generate_litepcie_software
            generate_litepcie_software(soc, os.path.join(builder.output_dir, "driver"))

        # Load FPGA bitstream ----------------------------------------------------------------------
        if args.load:
            board.load(filename=builder.get_bitstream_filename(mode="sram"))

        # Flash bitstream/images (to SPI Flash) ----------------------------------------------------
        if args.flash:
            board.flash(filename=builder.get_bitstream_filename(mode="flash"))

        # Generate SoC documentation ---------------------------------------------------------------
        if args.doc:
            soc.generate_doc(board_name)

if __name__ == "__main__":
    main()
