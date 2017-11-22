#!/usr/bin/env python3
"""
Assess MASH screening results.
"""
__author__ = "Fredrik Boulund"
__date__ = "2017"
__version__ = "0.1b"

from sys import argv, exit
from collections import namedtuple
import argparse
import logging

MashHit = namedtuple("MashHit", "identity shared_hashes median_multiplicity p_value query comment".split())

def parse_args():

    desc = "{desc} Copyright (c) {year} {author}.".format(desc=__doc__, year=__date__, author=__author__)
    epilog = "{doc}Version {ver}.".format(doc=__doc__, ver=__version__)
    parser = argparse.ArgumentParser(description=desc, epilog=epilog)
    parser.add_argument("screen", 
            help="MASH screen output.")
    parser.add_argument("-o", "--outfile", metavar="FILENAME", 
            default="mash_screen_assessment.txt", 
            help="Output filename [%(default)s].")

    dev = parser.add_argument_group("Developer options")
    dev.add_argument("--loglevel", 
            choices=["INFO","DEBUG"],
            default="INFO",
            help="Set logging level [%(default)s].")

    if len(argv) < 2:
        parser.print_help()
        exit(1)

    args = parser.parse_args()

    # Configure logging
    if args.loglevel == "INFO":
        loglevel = logging.INFO
    else:
        loglevel = logging.DEBUG

    logging.basicConfig(level=loglevel)

    return args 


def parse_screen(screen_file):
    with open(screen_file) as f:
        for line_number, line in enumerate(f, start=1):
            try:
                (identity, shared_hashes, median_multiplicity, 
                        p_value, query, comment) = line.strip().split("\t")
                mash_hit = MashHit(float(identity), 
                                   tuple(map(int, shared_hashes.split("/"))),
                                   int(median_multiplicity),
                                   float(p_value),
                                   query,
                                   comment)

            except ValueError:
                log.error("Could not parse line %s:\n %s", line_number, line)
            yield mash_hit


def get_top_hits(mash_hits, min_identity=0.85, min_shared_hashes_threshold=0.10):
    """
    Yield top ranked MASH screen hits.
    """

    sorted_mash_hits = sorted(mash_hits, key=lambda h: h.identity, reverse=True)
    best_hit_hash_proportion = sorted_mash_hits[0].shared_hashes[0] 

    logging.debug("Best match: %s", sorted_mash_hits[0])
    for hit in sorted_mash_hits:
        pass_identity = hit.identity > min_identity
        pass_hash_proportion = hit.shared_hashes[0] > min_shared_hashes_threshold * best_hit_hash_proportion
        if pass_identity and pass_hash_proportion:
            yield hit


def same_species(hits):
    """
    Determine if hits are from the same species.
    """
    if not isinstance(hits, list):
        hits = list(hits)
    found_species = set()
    for hit in hits:
        if hit.comment.startswith("["):
            splithit = hit.comment.split("]")[1]
        else:
            splithit = " ".join(hit.comment.split())
        found_species.add(" ".join(splithit.split()[1:3]))

    if len(found_species) > 1:
        print("Found more than one species! {}".format(found_species))
    else:
        print("The sample probably consist of only a single species: {}".format(list(found_species)[0]))


if __name__ == "__main__":
    args = parse_args()
    top_hits = get_top_hits(parse_screen(args.screen))
    same_species(top_hits)


