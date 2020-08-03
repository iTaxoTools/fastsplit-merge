# fastsplit-merge
Fastmerge and Fastsplit tools

## Installation
Installation is currently not intended. Downloading should be enough

## Generating an executable
Using [PyInstaller](http://www.pyinstaller.org) is recommended. After the following instruction a directory `dist` will be created (among other) and the executable will be inside it.

### Linux
Install PyInstaller from PyPI:

    pip install pyinstaller

Then run

    pyinstaller --onefile fastmerge.py

### Windows
Install PyInstaller:

[Installing on Windows](https://pyinstaller.readthedocs.io/en/stable/installation.html#installing-in-windows)

Then run

    pyinstaller --onefile --windowed fastmerge.py

## Fastmerge

### Usage
    usage: fastmerge.py [-h] [--cmd] [--fasta | --fastq] [--seqid PATTERN]
                        [--sequence PATTERN]
           fastmerge.py
    
    optional arguments:
      -h, --help          show this help message and exit
      --cmd               Launches in the command-line mode
      --fasta             Process only .fas and .fas.gz files
      --fastq             Process only .fq, .fq.gz, .fastq and .fastq.gz files
      --seqid PATTERN     Filter pattern for sequence names
      --sequence PATTERN  Filter pattern for sequences

### Command-line interface
Fastmerge reads the list of files and directories from the standard input and merges them into one file. For each directory, it merges the files inside it.
It uncompresses the gzip archives if necessary. The output is written to the standard output. 

When --seqid or --sequence and either --fasta or --fastq options are given, only the sequence records matching the patterns are written to the output.

## Filtering
A pattern consists of strings in double quotes, operators 'and', 'or' and 'not' (unquoted) and parentheses. It should be given in single quotes for the command-line interface and unquoted for the GUI.

Examples:
* "Boophis"
* not "Boophis"
* "Boophis" and "Madagascar"
* "Boophis" or "Madagascar"
* ("Boophis" or "Madagascar") and "Ranomafana"
