{
  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";

  outputs = { self, nixpkgs }: let
    inputs = { inherit nixpkgs; };
    system = "x86_64-linux";

    # a text file containing the paths to the flake inputs in order to stop
    # them from being garbage collected
    pleaseKeepMyInputs = pkgs.writeTextDir "bin/.please-keep-my-inputs"
      (builtins.concatStringsSep " " (builtins.attrValues inputs));

    pkgs = import nixpkgs {
      inherit system;
      config = { allowUnfree = true; };
      overlays = [
        (import ./nix/overlay.nix)
      ];
    };
  in {
    devShell."${system}" = pkgs.mkShell {
      buildInputs = [
        (pkgs.python3.withPackages (p: with p; [

        ]))

        pleaseKeepMyInputs
      ];
    };
  };
}
