#!/usr/bin/env python3

import multiprocessing

from itaxotools.fastsplit_merge import fastmerge_main

if __name__ == "__main__":
    multiprocessing.freeze_support()
    fastmerge_main()
