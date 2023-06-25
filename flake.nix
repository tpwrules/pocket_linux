{
  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";

  inputs.nix-litex.url = "git+https://git.sr.ht/~lschuermann/nix-litex?ref=main";
  inputs.nix-litex.flake = false;

  outputs = { self, nixpkgs, nix-litex }: let
    inputs = { inherit nixpkgs nix-litex; };
    system = "x86_64-linux";

    # a text file containing the paths to the flake inputs in order to stop
    # them from being garbage collected
    pleaseKeepMyInputs = pkgs.writeTextDir "bin/.please-keep-my-inputs"
      (builtins.concatStringsSep " " (builtins.attrValues inputs));

    nix-litex-pkgs = (import nix-litex { inherit pkgs; skipChecks = true; });

    pkgs = import nixpkgs {
      inherit system;
      config = { allowUnfree = true; };
      overlays = [
        (import ./nix/overlay.nix)
        (final: prev: {
          inherit (nix-litex-pkgs) mkSbtDerivation;

          python3 = prev.python3.override {
            packageOverrides = prev.lib.composeExtensions nix-litex-pkgs.pythonOverlay (p-final: p-prev: {
              litex-unchecked = p-prev.litex-unchecked.overrideAttrs (o: {
                patches = (o.patches or []) ++ [
                  ./nix/patches/litex-improve-jtagstream-transmission.patch
                  ./nix/patches/litex-nice-litex-term.patch
                ];
              });
            });
          };
        })
      ];
    };


  in {
    devShell."${system}" = pkgs.mkShell {
      buildInputs = [
        (pkgs.python3.withPackages (p: with p; [
          migen
          litex
          litex-boards
          litedram
          litespi
          pythondata-cpu-vexriscv
          pythondata-cpu-vexriscv_smp
          pythondata-software-compiler_rt
          pythondata-software-picolibc
          pyvcd
          pyserial
          requests
          packaging
        ]))

        pkgs.meson
        pkgs.ninja
        pkgs.pkgsCross.riscv64.buildPackages.gcc
        pkgs.dtc
        pkgs.unzip

        pkgs.openocd
        (pkgs.quartus-prime-lite.override {
          supportedDevices = [ "Cyclone V" ];
        })

        pleaseKeepMyInputs
      ];
    };
  };
}
