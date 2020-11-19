#!/usr/bin/python3

import argparse

parser = argparse.ArgumentParser()

parser.add_argument("server")
args = parser.parse_args()

print (args.server)
