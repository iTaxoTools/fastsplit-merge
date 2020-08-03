#!/usr/bin/env python3

import argparse
from lib.utils import *
from typing import Optional, List, cast, BinaryIO
import warnings
import sys


def parse_size(s: str) -> Optional[int]:
    """
    Parses file size as number with a suffix in "bBkKmMgG", interpreted as a unit
    """
    num = s[:-1]
    suffix = s[-1]
    try:
        power = dict(b=0, k=1, m=2, g=3)[suffix.casefold()]
    except KeyError:
        return None
    return int(num) * (1024 ** power)


def list_bytes(chunk: List[str]) -> bytes:
    """
    converts a list of string into utf-8 encoded bytes
    """
    return b''.join(map(lambda s: bytes(s, 'utf-8'), chunk))


def write_maxsize(chunks: Iterator[List[str]], maxsize: int, compressed: bool, output_template: str) -> None:
    """
    Writes chunks to the files based on the output_template, each file will be no bigger than maxsize.
    Each chunk will be written whole in some file.
    If 'compressed' each file will be compressed with gzip.
    """
    # generator of output files
    files = template_files(output_template, 'wb', compressed)
    # keep track of written size
    current_size = 0
    # current output file
    current_file = cast(BinaryIO, next(files))

    for chunk in chunks:
        # convert the chunk into bytes
        bytes_to_write = list_bytes(chunk)
        if current_size + len(bytes_to_write) > maxsize:
            # if the current file would overflow, switch to a new file
            current_file = cast(BinaryIO, next(files))
            current_size = 0
        # write the bytes and add the written size
        current_file.write(bytes_to_write)
        current_size = current_size + len(bytes_to_write)
    # close the last file
    try:
        files.send('stop')
    except StopIteration:
        pass


def fastsplit(file_format: str, split_n: Optional[int], maxsize: Optional[int], seqid_pattern: Optional[str], sequence_pattern: Optional[str], infile_path: Optional[str], compressed: bool, outfile_template: Optional[str]) -> None:
    if not infile_path:
        # raise error, if there is no input file
        raise ValueError("No input file")
    with open(infile_path) as infile:
        # prepare a valid output template
        if not outfile_template:
            outfile_template = make_template(infile_path)
        elif not '#' in outfile_template:
            outfile_template = make_template(outfile_template)
        # initialize the input file reader
        if file_format == 'fasta':
            chunks = fasta_iter_chunks(infile)
        elif file_format == 'fastq':
            chunks = fastq_iter_chunks(infile)
        # call subfunctions
        if maxsize:
            # split by maximum size
            write_maxsize(chunks, maxsize, compressed, outfile_template)
        elif split_n:
            # split by number of files
            # get the size of the input
            size = os.stat(infile_path).st_size
            # if split_n == 6, size == 42 gives maxsize == 7, size == 43 gives maxsize == 8, size 48 gives maxsize 8
            maxsize = (size - 1 + split_n) // split_n
            write_maxsize(chunks, maxsize, compressed, outfile_template)


argparser = argparse.ArgumentParser()

format_group = argparser.add_mutually_exclusive_group()
format_group.add_argument('--fasta', dest='format', action='store_const',
                          const='fasta', help='Input file is a fasta file')
format_group.add_argument('--fastq', dest='format', action='store_const',
                          const='fastq', help='Input file is a fastq file')

split_group = argparser.add_mutually_exclusive_group()
split_group.add_argument('--split_n', type=int,
                         help='number of files to split into')
split_group.add_argument('--maxsize', type=parse_size,
                         help='Maximum size of output file')

argparser.add_argument('--compressed', action='store_true',
                       help='Compress output files with gzip')
argparser.add_argument('infile', nargs='?', help='Input file name')
argparser.add_argument('outfile', nargs='?', help='outfile file template')


args = argparser.parse_args()

if not args.format:
    pass
    # launch_gui()
else:
    try:
        with warnings.catch_warnings(record=True) as warns:
            fastsplit(args.format, args.split_n, args.maxsize, None,
                      None, args.infile, args.compressed, args.outfile)
            for w in warns:
                print(w.message)
    except ValueError as ex:
        sys.exit(ex)
