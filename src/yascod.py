#!/usr/bin/env python3
import subprocess as sp
import argparse
import logging

import libvirt
import etcd3


#
# Cluster Distribution Map (CMD), and its failure variations
# to handle fault situations
#
CDM = {
    "quark": [  # Ilya's node
        "freebsd-vmm2",
        "win7-vmm2",
    ],
    "snailin": [  # Ayrat's node
        "test",
        "ubuntu-vmm2",
    ],
}
CDM_fallbacks = {
    "quark": {  # if Ilya's node is down
        "quark": [],
        "snailin": [
            "freebsd-vmm2",
            "win7-vmm2",
            "test",
            "ubuntu-vmm2",
        ],
    },
    "snailin": {  # if Ayrat's node is down
        "quark": [
            "freebsd-vmm2",
            "win7-vmm2",
            "test",
            "ubuntu-vmm2",
        ],
        "snailin": [],
    },
}
Cur_CDM = CDM


def is_host_alive(hostname: str):
    """
    Check that the host with Hostname is still in the cluster
    """
    ping_pc = sp.run(args=["ping", "-c", "1", hostname],
                     stdout=sp.PIPE, stderr=sp.PIPE)
    return ping_pc.returncode == 0



def parse_args():
    parser = argparse.ArgumentParser(
        "yascod - PoC daemon for the cluster knapsack problem")
    parser.add_argument("--domains-path", type=str, default="/srv/domains")
    parser.add_argument("--log", type=str, default="WARNING")

    args = parser.parse_args()

    numeric_level = getattr(logging, args.log.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError('Invalid log level: %s' % args.log)

    logging.basicConfig(level=numeric_level,
                        format='%(asctime)s %(levelname)s %(message)s')

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    logging.info("The yascod has started with --domains-path: %s",
                 args.domains_path)
    logging.warning(
        "It is Proof-of-Concept. Daemon works only in debug foreground process")
