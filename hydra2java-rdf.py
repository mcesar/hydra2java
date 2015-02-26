#!/usr/bin/python

import sys
import json
import types
import argparse

from rdflib import RDF, RDFS, XSD, Graph, URIRef, Literal, Namespace
from rdflib.parser import Parser
import rdfextras

rdfextras.registerplugins()

HYDRA = Namespace('http://www.w3.org/ns/hydra/core#')

prefix_mapping = {
	XSD.string: 'String',
	XSD.boolean: 'boolean',
	XSD.dateTime: 'java.util.Date',
	HYDRA.Collection: 'java.util.Collection',
	'http://www.w3.org/2002/07/owl#Nothing': 'void'
}

def main():
	parser = argparse.ArgumentParser()
	parser.add_argument("-f", "--format", default="json-ld")
	args = parser.parse_args()
	g = Graph().parse(sys.stdin, format=args.format)
	api = g.value(None, RDF.type, HYDRA.ApiDocumentation)
	prefix_mapping[api] = ''
	for c in g.objects(api, HYDRA.supportedClass):
		generate_class(g, api, c)

def generate_class(g, api, c):
	if not c.startswith(api):
		return
	class_label = replace_prefix(prefix_mapping, c)
	print('public interface {} {{'.format(class_label))
	for sp in g.objects(c, HYDRA.supportedProperty):
		p = g.value(sp, HYDRA.property)
		prop_label = replace_prefix(prefix_mapping, p)
		if '_' in prop_label:
			prop_label = ''.join([ l.capitalize() for l in prop_label.split('_') ])
		else:
			prop_label = prop_label[0].upper() + prop_label[1:len(prop_label)]
		prop_type = replace_prefix(prefix_mapping, g.value(p, RDFS.range))
		read_only = Literal(True).eq(g.value(sp, HYDRA.readonly))
		write_only = Literal(True).eq(g.value(sp, HYDRA.writeonly))
		prop_operations = g.objects(p, HYDRA.supportedOperation)
		no_operations = generate_methods(g, prop_label, prop_type, prop_operations)
		if no_operations:
			generate_property(prop_label, prop_type, read_only, write_only)
	generate_methods(g, class_label, class_label, g.objects(c, HYDRA.supportedOperation))
	print('}')

def replace_prefix(prefix_mapping, uri):
	if isinstance(uri, (list, types.GeneratorType)):
		result = []
		for each in uri:
			result.append(replace_prefix(prefix_mapping, each))
		return result
	result = uri
	for prefix in prefix_mapping.keys():
		if result.startswith(prefix):
			result = result.replace(prefix, prefix_mapping[prefix])
			if '#' in result:
				result = result.rpartition('#')[2]
			if '/' in result:
				result = result.rpartition('/')[2]
	return result

def generate_methods(g, label, class_type, operations):
	no_operations = True
	for so in operations:
		method_name = g.value(so, HYDRA.method)
		expects = replace_prefix(prefix_mapping, g.objects(so, HYDRA.expects))
		returns = replace_prefix(prefix_mapping, g.objects(so, HYDRA.returns))
		generate_method(label, class_type, method_name, expects, returns)
		no_operations = False
	return no_operations

def generate_property(label, prop_type, read_only, write_only):
	if not write_only: print('    {} get{}()'.format(prop_type, label))
	if not read_only: print('    void set{}({} {})'.format(label, prop_type, label[0].lower() + label[1:len(label)]))

def generate_method(label, prop_type, method_name, expects, returns):
	args = ', '.join([ e + ' '+ e[0].lower() + e[1:len(e)] for e in expects ])
	if Literal('GET').eq(method_name):
		print('    {} get{}({})'.format(returns[0], label, args))
	elif Literal('PUT').eq(method_name):
		print('    {} set{}({})'.format(returns[0], label, args))
	elif Literal('POST').eq(method_name) and prop_type == prefix_mapping[HYDRA.Collection]:
	 	print('    {} addTo{}({})'.format(returns[0], label, args))
	elif Literal('POST').eq(method_name) and prop_type == HYDRA.Resource:
		print('    {} {}({})'.format(returns[0], label, args))
	elif Literal('DELETE').eq(method_name):
		print('    {} remove{}({})'.format(returns[0], label, args))
	else:
		raise Exception('Operation not supported:', label, prop_type, expects, returns, method_name)

if __name__ == '__main__':
	main()