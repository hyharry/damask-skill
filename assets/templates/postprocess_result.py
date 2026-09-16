#!/usr/bin/env python3
"""Minimal DAMASK result-inspection template; copy before editing."""

from __future__ import annotations

import argparse

import damask


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect a DAMASK DADF5/HDF5 result.")
    parser.add_argument("result", help="result HDF5 file")
    parser.add_argument(
        "--increment",
        type=int,
        help="show one increment; omit to keep the complete result view",
    )
    args = parser.parse_args()

    result = damask.Result(args.result)
    if args.increment is not None:
        result = result.view(increments=args.increment)
    print(result)


if __name__ == "__main__":
    main()
