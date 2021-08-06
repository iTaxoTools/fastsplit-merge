#!/usr/bin/env python3

import multiprocessing

from itaxotools.fastsplit_merge import fastsplit_main

if __name__ == "__main__":
    multiprocessing.freeze_support()
    fastsplit_main()