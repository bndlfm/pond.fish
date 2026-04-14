{
  description = "fish-ai: AI functionality for Fish shell";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs?ref=nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs { inherit system; };
      in
      {
        devShells.default = pkgs.mkShell {
          buildInputs = [
            pkgs.python311
            pkgs.fish
            pkgs.uv
            pkgs.fzf
            pkgs.python311Packages.rich
          ];

          shellHook = ''
            echo "🐠 Welcome to the fish-ai development environment (Nix Edition)!"
            
            # Setup virtual environment with uv if it doesn't exist
            if [ ! -d ".venv" ]; then
              echo "📦 Creating virtual environment and installing dependencies..."
              uv venv
              uv pip install -e .
              uv pip install pytest
            fi
            
            # Source activation if using bash, else rely on uv run
            if [ -n "$BASH_VERSION" ]; then
              source .venv/bin/activate
            fi
            
            export PYTHONPATH="$PYTHONPATH:$(pwd)/src"
            export PATH="$(pwd)/.venv/bin:$PATH"
            
            echo "✅ Environment ready. Run 'pytest' to verify."
          '';
        };
      });
}
