#!/usr/bin/env python3
import argparse
import logging


def parse_args():
    parser = argparse.ArgumentParser(
        "yascod - PoC daemon for the cluster knapsack problem")
    parser.add_argument("--domains-path", type=str, default="/srv/domains")
    parser.add_argument("--log", type=str, default="WARNING")

    args = parser.parse_args()

    numeric_level = getattr(logging, args.log.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError('Invalid log level: %s' % args.log)

    logging.basicConfig(level=numeric_level, filename="example.log",
                        format='%(asctime)s %(levelname)s %(message)s')

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    logging.info("The yascod has started with --domains-path: %s",
                 args.domains_path)
    logging.warning(
        "It is Proof-of-Concept. Daemon works only in debug foreground process")
