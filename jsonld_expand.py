#!/usr/local/bin/python3

from pyld import jsonld
import json
import sys

def main():
	doc = json.load(sys.stdin)
	expanded = jsonld.expand(doc)
	print(json.dumps(expanded, indent=2))

if __name__ == '__main__':
	main()