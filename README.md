### Linux on the Analogue Pocket

This proof of proof of concept uses [LiteX](https://github.com/enjoy-digital/litex) to generate a RISC-V SoC which runs a full Linux kernel and (presently) basic busybox userland. No Analogue Pocket Framework code is used at all.

Pre-built binaries are not yet available. To do this yourself, you'll need to install the [core-template](https://github.com/open-fpga/core-template/releases/tag/v1.0.0) on your Pocket to get the Pocket in a state where you can download the SoC over JTAG. You'll also need an x86_64 Linux system with the [Nix package manager](https://nixos.org/download.html) installed. No other dependencies are necessary. A sketch of the required commands is available in the `docs/` directory of the repo.

This is really just an excuse to get familiar with LiteX and see how it can be integrated with Nix. Any similarity to or use as an entertainment product or system is purely coincidental and we cannot be held responsible in the event you have any fun.
