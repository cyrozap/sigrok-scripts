#!/usr/bin/env python3
# SPDX-License-Identifier: 0BSD

# Copyright (C) 2020, 2025 by Forest Crossman <cyrozap@gmail.com>
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
import sys
from dataclasses import dataclass
from enum import auto, Enum
from io import TextIOWrapper
from typing import Iterable


@dataclass
class Buffer:
    addr: int
    data: bytes

class State(Enum):
    INIT = auto()
    ADDR_WRITE = auto()
    ADDR_READ = auto()


def parse_args() -> argparse.Namespace:
    parser: argparse.ArgumentParser = argparse.ArgumentParser(description="Convert I2C text log to binary.")
    parser.add_argument("-a", "--address", type=lambda x: int(x, 16), default=0x50,
                        help="EEPROM address in hexadecimal (default: 0x50).")
    parser.add_argument("file", nargs="?", type=argparse.FileType("r"), default=sys.stdin,
                        help="Input I2C log file. If not specified, reads from stdin.")
    return parser.parse_args()

def i2c_log_to_bin(lines: Iterable[str], address: int) -> bytes:
    state: State = State.INIT
    addr: int = 0
    bufs: list[Buffer] = []
    bufs_idx: int = 0
    for line in lines:
        line_parts: list[str] = line.strip("\n").split(": ")
        if line_parts[1:] == ["Address write", f"{address:02X}"]:
            state = State.ADDR_WRITE
            addr = 0
            continue
        elif line_parts[1:] == ["Address read", f"{address:02X}"]:
            state = State.ADDR_READ
            bufs.append(Buffer(addr=addr, data=b""))
            bufs_idx += 1
            continue

        if state == State.ADDR_WRITE:
            if line_parts[1] == "Data write":
                addr = ((addr << 8) & 0xffff) | bytes.fromhex(line_parts[2])[0]
        elif state == State.ADDR_READ:
            if line_parts[1] == "Data read":
                bufs[bufs_idx-1].data += bytes.fromhex(line_parts[2])

    length: int = 0
    for buf in bufs:
        new_len: int = buf.addr + len(buf.data)
        if new_len > length:
            length = new_len

    binary: bytearray = bytearray(b"\xff" * length)
    for buf in bufs:
        binary[buf.addr:buf.addr+len(buf.data)] = buf.data

    return bytes(binary)

def main() -> None:
    args: argparse.Namespace = parse_args()

    logfile: TextIOWrapper = args.file

    binary: bytes = i2c_log_to_bin(logfile, args.address)

    sys.stdout.buffer.write(binary)


if __name__ == "__main__":
    main()
