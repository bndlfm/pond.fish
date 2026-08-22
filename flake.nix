{
  description = "Pond: stateful ACP functionality for Fish shell";

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
            echo "🐠 Welcome to the Pond development environment (Nix Edition)!"
            
            # Recreate a stale/garbage-collected Nix venv as well as an absent one.
            # Checking only the directory leaves broken console-script shebangs behind.
            if [ ! -x ".venv/bin/python" ]; then
              echo "📦 Creating virtual environment and installing dependencies..."
              uv venv --clear --python "$(command -v python)" .venv
              uv pip install --python .venv/bin/python -e . -r .devcontainer/requirements-dev.txt
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
