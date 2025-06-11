#!/usr/bin/env python3
# SPDX-License-Identifier: 0BSD

# Copyright (C) 2025 by Forest Crossman <cyrozap@gmail.com>
#
# Permission to use, copy, modify, and/or distribute this software for
# any purpose with or without fee is hereby granted.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL
# WARRANTIES WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE
# AUTHOR BE LIABLE FOR ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL
# DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR
# PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR OTHER
# TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR
# PERFORMANCE OF THIS SOFTWARE.


import argparse
import re
import sys
from io import TextIOWrapper
from typing import Iterable, NamedTuple


class Transaction(NamedTuple):
    addr: int
    data: bytes

class DataAndMask(NamedTuple):
    data: bytes
    mask: bytes


def parse_args() -> argparse.Namespace:
    parser: argparse.ArgumentParser = argparse.ArgumentParser(description="Generate binary and mask files from SPI transaction log.")
    parser.add_argument("-m", "--output-mask",
                        help="Output mask file (binary, 0xFF where data was written).")
    parser.add_argument("file", nargs="?", type=argparse.FileType("r"), default=sys.stdin,
                        help="Input SPI log file. If not specified, reads from stdin.")
    return parser.parse_args()

def parse_spi_transaction(line: str) -> Transaction | None:
    match: re.Match | None = re.match(r"spiflash-1: Read data \(addr 0x([0-9a-fA-F]+), (\d+) bytes\): ([\s\w]+)", line)
    if not match:
        return None

    addr: int = int(match.group(1), 16)
    length: int = int(match.group(2))
    data_hex: str = match.group(3).strip().replace(" ", "")

    if len(data_hex) != 2 * length:
        return None

    try:
        data_bytes = bytes.fromhex(data_hex)
    except ValueError:
        return None

    if len(data_bytes) != length:
        return None

    return Transaction(addr, data_bytes)

def spi_log_to_bin(lines: Iterable[str]) -> DataAndMask:
    binary: bytearray = bytearray()
    mask: bytearray = bytearray()

    for line in lines:
        result: Transaction | None = parse_spi_transaction(line)
        if result is None:
            continue

        length: int = len(result.data)
        required_size: int = result.addr + length
        current_size: int = len(binary)
        if required_size > current_size:
            delta: int = required_size - current_size
            binary.extend([0] * delta)
            mask.extend([0] * delta)

        addr: int = result.addr
        binary[addr:addr+length] = result.data
        mask[addr:addr+length] = [0xFF] * length

    return DataAndMask(bytes(binary), bytes(mask))

def main() -> int:
    args: argparse.Namespace = parse_args()

    logfile: TextIOWrapper = args.file

    data_and_mask: DataAndMask = spi_log_to_bin(logfile)

    if not data_and_mask.data:
        print("No data found in the input file.", file=sys.stderr)
        return 1

    sys.stdout.buffer.write(data_and_mask.data)

    if args.output_mask:
        try:
            with open(args.output_mask, "wb") as f:
                f.write(data_and_mask.mask)
            print(f"Mask image written to {args.output_mask}", file=sys.stderr)
        except Exception as e:
            print(f"Error writing mask file: {e}", file=sys.stderr)
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
