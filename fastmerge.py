#!/usr/bin/env python3

from lib.utils import *
from typing import Iterator, Union, TextIO, cast
import os
import argparse
import gzip
import warnings
import sys

# extensions of the fasta files
fasta_exts = {'.fas'}
# extensions of the fastq files
fastq_exts = {'.fq', '.fastq'}


def fastmerge(file_list: Iterator[str], file_types: List[str], seqid_pattern: str, sequence_pattern: str, output: TextIO) -> None:
    """
    Main merging function
    """
    if not file_types:
        fastmerge_pure(file_list, output)
    else:
        if seqid_pattern or sequence_pattern:
            if '.fas' in file_types:
                fastmerge_fasta_filter(file_list, parse_pattern_optional(seqid_pattern),
                                       parse_pattern_optional(sequence_pattern), output)
            else:
                fastmerge_fastq_filter(file_list, parse_pattern_optional(seqid_pattern),
                                       parse_pattern_optional(sequence_pattern), output)
        else:
            fastmerge_type(file_list, file_types, output)


def parse_pattern_optional(pattern: Optional[str]) -> Optional[Pattern]:
    if pattern:
        return Pattern(pattern)
    else:
        return None


def ext_gz(path: Union[str, os.PathLike]) -> str:
    """
    Returns the extension, returns internal extension for gzip archives
    """
    root, ext = os.path.splitext(path)
    if ext == '.gz':
        _, ext = os.path.splitext(root)
    return ext


def list_files(file_list: Iterator[str]) -> Iterator[Union[str, os.DirEntry]]:
    """
    For each file in 'file_list' yield its name.
    For each directory, yields the DirEnty of file inside it
    """
    for filename in file_list:
        filename = filename.strip()
        if os.path.isdir(filename):
            for entry in filter(os.DirEntry.is_file, os.scandir(filename)):
                yield entry
        elif os.path.exists(filename):
            yield filename


def fastmerge_pure(file_list: Iterator[str], output: TextIO) -> None:
    """
    Merge the files, extracting all gzip archives
    """
    for entry in list_files(file_list):
        # open the file as archive or text file
        if os.path.splitext(entry)[1] == '.gz':
            file = cast(TextIO, gzip.open(entry, mode='rt'))
        else:
            file = open(entry)
        # copy the lines to the output
        with file:
            for line in file:
                output.write(line)


def fastmerge_type(file_list: Iterator[str], file_types: List[str], output: TextIO) -> None:
    """
    Merge the file only of the given 'file_types', extracting all gzip archives
    """
    for entry in list_files(file_list):
        # skip the files of the wrong type
        if not ext_gz(entry) in file_types:
            continue
        # open the file as archive or text file
        if os.path.splitext(entry)[1] == '.gz':
            file = cast(TextIO, gzip.open(entry, mode='rt'))
        else:
            file = open(entry)
        # copy the lines to the output
        with file:
            for line in file:
                output.write(line)


def fastmerge_fasta_filter(file_list: Iterator[str], seqid_pattern: Optional[Pattern], sequence_pattern: Optional[Pattern], output: TextIO) -> None:
    """
    Merge the fasta files, extraction all gzip archives.
    Filter records with the given patterns
    """
    print(sequence_pattern)
    for entry in list_files(file_list):
        # skip the files of the wrong type
        if not ext_gz(entry) in fasta_exts:
            continue
        # copy the lines to the output
        if os.path.splitext(entry)[1] == '.gz':
            file = cast(TextIO, gzip.open(entry, mode='rt'))
        else:
            file = open(entry)
        with file:
            # warn about the line breaks
            line_breaks_warned = False
            for seqid, sequence in fasta_iter(file):
                if not line_breaks_warned and sequence_pattern and len(sequence) > 1:
                    line_breaks_warned = True
                    warnings.warn(f"The file {file.name} contains sequences interrupted with line breaks, and the search for sequence motifs will not work reliably in this case - some sequences with the specified motif will likely be missed. Please first transform your file into a fasta file without line breaks interrupting the sequences.")
                # skip sequences that don't match the seqid pattern
                if seqid_pattern:
                    if not seqid_pattern.match(seqid):
                        continue
                # skip sequences that don't match the sequence pattern
                if sequence_pattern:
                    if not any(map(sequence_pattern.match, sequence)):
                        continue
                # copy the lines into the output
                output.write(seqid)
                for chunk in sequence:
                    output.write(chunk)


def fastmerge_fastq_filter(file_list: Iterator[str], seqid_pattern: Optional[Pattern], sequence_pattern: Optional[Pattern], output: TextIO) -> None:
    """
    Merge the fastq files, extraction all gzip archives.
    Filter records with the given patterns
    """
    for entry in list_files(file_list):
        # skip the files of the wrong type
        if not ext_gz(entry) in fastq_exts:
            continue
        # copy the lines to the output
        if os.path.splitext(entry)[1] == '.gz':
            file = cast(TextIO, gzip.open(entry, mode='rt'))
        else:
            file = open(entry)
        with file:
            for seqid, sequence, quality_score_seqid, quality_score in fastq_iter(file):
                # skip sequences that don't match the seqid pattern
                if seqid_pattern:
                    if not seqid_pattern.match(seqid):
                        continue
                # skip sequences that don't match the sequence pattern
                if sequence_pattern:
                    if not sequence_pattern.match(sequence):
                        continue
                output.write(seqid)
                output.write(sequence)
                output.write(quality_score_seqid)
                output.write(quality_score)


argparser = argparse.ArgumentParser()
argparser.add_argument('--cmd', action='store_true',
                       help="Launches in the command-line mode")
format_group = argparser.add_mutually_exclusive_group()
format_group.add_argument('--fasta', dest='ext', action='store_const', const=fasta_exts,
                          help="Process only .fas and .fas.gz files")
format_group.add_argument('--fastq', dest='ext', action='store_const', const=fastq_exts,
                          help="Process only .fq, .fq.gz, .fastq and .fastq.gz files")
argparser.add_argument('--seqid', metavar='PATTERN',
                       help="Filter pattern for sequence names")
argparser.add_argument('--sequence', metavar='PATTERN',
                       help="Filter pattern for sequences")

args = argparser.parse_args()

try:
    with warnings.catch_warnings(record=True) as warns:
        fastmerge(sys.stdin, args.ext,
                  args.seqid, args.sequence, sys.stdout)
        for w in warns:
            print(w.message)
except ValueError as ex:
    sys.exit(ex)
