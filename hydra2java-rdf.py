#!/usr/bin/python

import argparse
import sys
import hydra2java_lib

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-f", "--format", default="json-ld")
    parser.add_argument("-t", "--type", default="interface")
    parser.add_argument("-p", "--package", default="")
    parser.add_argument("-d", "--destination", default="")
    parser.add_argument("-a", "--no_annotations", action="store_true", default=False)
    parser.add_argument("-m", "--members", default="all")
    parser.add_argument("-l", "--delegate", action="store_true", default=False)
    parser.add_argument("-s", "--supplemental_annotations", default="")
    parser.add_argument("-c", "--collection_implementation", default="")
    args = parser.parse_args()
    gen = hydra2java_lib.Generator(args.format, args.type, args.package, args.destination,
            args.no_annotations, args.members, args.delegate, args.supplemental_annotations,
            args.collection_implementation)
    gen.generate(sys.stdin)

if __name__ == '__main__':
    main()
