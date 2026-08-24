{ pkgs }:
pkgs.fish.overrideAttrs (old: {
  patches = (old.patches or []) ++ [
    ./fish-command-capture.patch
  ];
})
