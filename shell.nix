# Nix development environment for beancount-periodic
#
# Usage:
#   nix-shell                    # Enter the development environment
#   nix-shell --run "pytest"     # Run a command in the environment

{ pkgs ? import <nixpkgs> {} }:

let
  # Python environment with all dependencies
  pythonEnv = pkgs.python312.withPackages (ps: with ps; [
    # Production dependencies (from requirements.txt)
    beancount      # >=2.3.4 - Core beancount library
    beangulp       # >=0.1.1 - Beancount ingestion framework
    python-dateutil # ~=2.9.0 - Date handling utilities

    # Development dependencies (from dev-requirements.txt)
    pytest         # Testing framework
    twine          # Package publishing tool

    # Build tools
    setuptools     # Package building
    wheel          # Wheel package format support
    pip            # Package installer
  ]);

in pkgs.mkShell {
  packages = [
    pythonEnv
    pkgs.pipreqs  # Requirements file generator
  ];
}
