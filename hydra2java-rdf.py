#!/usr/bin/python

import sys
import json
import types
import argparse
import os

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
	parser.add_argument("-t", "--type", default="interface")
	parser.add_argument("-p", "--package", default="")
	parser.add_argument("-d", "--destination", default="")
	parser.add_argument("-a", "--no_annotations", action="store_true", default=False)
	args = parser.parse_args()
	g = Graph().parse(sys.stdin, format=args.format)
	api = g.value(None, RDF.type, HYDRA.ApiDocumentation)
	prefix_mapping[api] = ''
	f = sys.stdout
	for c in g.objects(api, HYDRA.supportedClass):
		if not c.startswith(api):
			continue
		if args.destination != '':
			f = file('{}{}{}.java'.format(args.destination, os.sep, class_label(c)), 'w')
		generate_class(g, api, c, args.package, args.type, f, args.no_annotations)
		if args.destination != '':
			f.close()

def generate_class(g, api, c, package, type_label, f, no_annotations):
	cl = class_label(c)
	if package != '':
		f.write('package {};\n\n'.format(package))

	if not no_annotations:
		f.write('import javax.ws.rs.GET;\n')
		f.write('import javax.ws.rs.POST;\n')
		f.write('import javax.ws.rs.PUT;\n')
		f.write('import javax.ws.rs.DELETE;\n')
		f.write('import javax.ws.rs.Consumes;\n')
		f.write('import javax.ws.rs.Path;\n')
		f.write('import javax.ws.rs.Produces;\n\n')
		f.write('@Path("{}")\n'.format(cl))

	f.write('public {} {}{{\n'.format(type_label, cl))
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
		if g.value(p, RDF.type, None) == HYDRA.Link:
			operations = list(g.objects(p, HYDRA.supportedOperation))
			generate_methods(g, prop_label, prop_type, operations, 
				[ prop_label + '/' + str(o) for o in operations ], type_label, f, no_annotations)
		else:
			generate_property(prop_label, prop_type, read_only, write_only, type_label, f)
	operations = list(g.objects(c, HYDRA.supportedOperation))
	generate_methods(g, cl, cl, operations, [ str(o) for o in operations ], type_label, f, no_annotations)
	f.write('}\n')

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

def generate_methods(g, label, class_type, operations, paths, type_label, f, no_annotations):
	no_operations = True
	for i, so in enumerate(operations):
		method_name = g.value(so, HYDRA.method)
		expects = replace_prefix(prefix_mapping, g.objects(so, HYDRA.expects))
		returns = replace_prefix(prefix_mapping, g.objects(so, HYDRA.returns))
		generate_method(label, class_type, method_name, expects, returns, paths[i], type_label, f, no_annotations)
		no_operations = False
	return no_operations

def generate_property(label, prop_type, read_only, write_only, type_label, f):
	if not write_only: 
		f.write('\n    {}{} get{}(){}\n'.format(access_level(type_label), prop_type, label, 
			sufix(type_label, prop_type)))
	if not read_only: 
		f.write('\n    {}void set{}({} {}){}\n'.format(access_level(type_label), label, prop_type, 
			label[0].lower() + label[1:len(label)], sufix(type_label, 'void')))

def generate_method(label, prop_type, method_name, expects, returns, path, type_label, f, no_annotations):
	args = ', '.join([ e + ' '+ e[0].lower() + e[1:len(e)] for e in expects ])
	annotations = ''
	if Literal('GET').eq(method_name):
		if not no_annotations:
			annotations = '    @GET @Path("{}")\n    @Produces("application/ld+json")\n'.format(path)
		f.write('\n{}    {}{} get{}({}){}\n'.format(annotations, access_level(type_label), returns[0], label, args, 
			sufix(type_label, returns[0])))
	elif Literal('PUT').eq(method_name):
		if not no_annotations:
			annotations = '    @PUT @Path("{}")\n    @Consumes("application/ld+json")\n    @Produces("application/ld+json")\n'.format(path)
		f.write('\n{}    {}{} set{}({}){}\n'.format(annotations, access_level(type_label), returns[0], label, args, 
			sufix(type_label, returns[0])))
	elif Literal('POST').eq(method_name) and prop_type == prefix_mapping[HYDRA.Collection]:
		if not no_annotations:
			annotations = '    @POST @Path("{}")\n    @Consumes("application/ld+json")\n    @Produces("application/ld+json")\n'.format(path)
	 	f.write('\n{}    {}{} addTo{}({}){}\n'.format(annotations, access_level(type_label), returns[0], label, args, sufix(type_label, returns[0])))
	elif Literal('POST').eq(method_name) and prop_type == HYDRA.Resource:
		if not no_annotations:
			annotations = '    @POST @Path("{}")\n    @Consumes("application/ld+json")\n    @Produces("application/ld+json")\n'.format(path)
		f.write('\n{}    {}{} {}({}){}\n'.format(annotations, access_level(type_label), returns[0], label, args, 
			sufix(type_label, returns[0])))
	elif Literal('DELETE').eq(method_name):
		if not no_annotations:
			annotations = '    @DELETE @Path("{}")\n    @Consumes("application/ld+json")\n    @Produces("application/ld+json")\n'.format(path)
		f.write('\n{}    {}{} remove{}({}){}\n'.format(annotations, access_level(type_label), returns[0], label, args, 
			sufix(type_label, returns[0])))
	else:
		raise Exception('Operation not supported:', label, prop_type, expects, returns, method_name)

def sufix(type_label, returns):
	if type_label == 'class':
		if returns == 'void':
			return ' {}'
		elif returns == 'boolean':
			return ' { return false; }'
		else:
			return ' { return null; }'
	else:
		return ';'

def access_level(type_label):
	if type_label == 'class':
		return 'public '
	else:
		return ''	

def class_label(c):
	return replace_prefix(prefix_mapping, c)

if __name__ == '__main__':
	main()