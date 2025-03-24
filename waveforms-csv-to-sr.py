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
import csv
import struct
import time
import zipfile
from pathlib import Path
from typing import Iterator


def get_zipinfo_with_extended_time(filename: str, mtime: float) -> zipfile.ZipInfo:
    # Set the DOS modification time to UTC
    date_time: tuple[int, int, int, int, int, int] = time.gmtime(mtime)[:6]

    # Create the ZipInfo object
    zi: zipfile.ZipInfo = zipfile.ZipInfo(filename, date_time)

    # Add extended timestamp with the Unix modification time
    zi.extra += struct.pack("<HHBI", 0x5455, 5, 0x01, int(mtime))

    return zi

def main() -> None:
    parser: argparse.ArgumentParser = argparse.ArgumentParser()
    parser.add_argument("csv", type=str, help="The input CSV file (WaveForms \"Raw Data\" format).")
    parser.add_argument("output", type=str, help="The sigrok srzip output file.")
    args: argparse.Namespace = parser.parse_args()

    csv_file: Path = Path(args.csv)
    mtime: float = csv_file.stat().st_mtime

    lines: list[str] = csv_file.open("r").readlines()
    header: list[str] = lines[:6]
    csv_data: list[str] = lines[8:]

    header_type: str = header[0]
    assert header_type.rstrip("\n") == "#Digilent WaveForms Logic Analyzer Raw Data"

    sample_rate: int = int(float(header[4].rstrip("Hz\n").split(": ")[1]))
    sample_count: int = int(header[5].rstrip("\n").split(": ")[1])
    assert sample_count == len(csv_data)
    unit_size: int = 2
    logic: bytearray = bytearray(sample_count * unit_size)

    offset: int = 0
    reader: Iterator[list[str]] = csv.reader(csv_data)
    for (timestamp, sample) in reader:
        struct.pack_into("<H", logic, offset, int(sample))
        offset += unit_size

    probe_count: int = 16
    probes: str = "\n".join(["probe{}=DIO {}".format(i+1, i) for i in range(probe_count)])
    metadata: str = "\n".join([
        "[global]",
        "sigrok version=0.5.0",
        "",
        "[device 1]",
        "capturefile=logic-1",
        f"total probes={probe_count}",
        f"samplerate={sample_rate//1_000_000} MHz",
        "total analog=0",
        probes,
        f"unitsize={unit_size}",
        "",
    ])

    sr: zipfile.ZipFile = zipfile.ZipFile(args.output, "w")
    sr.writestr(get_zipinfo_with_extended_time("version", mtime), "2", zipfile.ZIP_STORED)
    sr.writestr(get_zipinfo_with_extended_time("metadata", mtime), metadata, zipfile.ZIP_DEFLATED)
    sr.writestr(get_zipinfo_with_extended_time("logic-1-1", mtime), logic, zipfile.ZIP_DEFLATED)
    sr.close()


if __name__ == "__main__":
    main()
