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
import zipfile


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("csv", type=str, help="The input CSV file (WaveForms \"Raw Data\" format).")
    parser.add_argument("output", type=str, help="The sigrok srzip output file.")
    args = parser.parse_args()

    lines = open(args.csv, 'r').readlines()
    header = lines[:6]
    csvfile = lines[8:]

    sample_rate = int(float(header[4].rstrip('Hz\n').split(': ')[1]))
    sample_count = int(header[5].rstrip('\n').split(': ')[1])
    assert sample_count == len(csvfile)
    unit_size = 2
    logic = bytearray(sample_count * unit_size)

    offset = 0
    reader = csv.reader(csvfile)
    for (timestamp, sample) in reader:
        struct.pack_into('<H', logic, offset, int(sample))
        offset += unit_size

    probe_count = 16
    probes = "\n".join(["probe{}=DIO {}".format(i+1, i) for i in range(probe_count)])
    metadata = "[global]\nsigrok version=0.5.0\n\n[device 1]\ncapturefile=logic-1\ntotal probes={}\nsamplerate={} MHz\ntotal analog=0\n{}\nunitsize={}\n".format(probe_count, sample_rate//1000000, probes, unit_size)

    sr = zipfile.ZipFile(args.output, 'w', zipfile.ZIP_DEFLATED)
    sr.writestr('version', '2', zipfile.ZIP_STORED)
    sr.writestr('metadata', metadata)
    sr.writestr('logic-1-1', logic)
    sr.close()


if __name__ == "__main__":
    main()
