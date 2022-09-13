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

    nix-litex-pkgs = (import nix-litex { inherit pkgs; sbtNixpkgs = pkgs; skipChecks = true; });

    pkgs = import nixpkgs {
      inherit system;
      config = { allowUnfree = true; };
      overlays = [
        (import ./nix/overlay.nix)
        (final: prev: {
          inherit (nix-litex-pkgs) sbt-mkDerivation;

          python3 = prev.python3.override {
            packageOverrides = nix-litex-pkgs.pythonOverlay;
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
          pythondata-cpu-vexriscv_smp
          pyvcd
        ]))

        pkgs.pkgsCross.riscv64.buildPackages.gcc

        (pkgs.quartus-prime-lite.override {
          supportedDevices = [ "Cyclone V" ];
        })

        pleaseKeepMyInputs
      ];
    };
  };
}
