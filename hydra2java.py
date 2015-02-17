#!/usr/local/bin/python3

import sys
import json

hydra = {
	'ApiDocumentation': 'http://www.w3.org/ns/hydra/core#ApiDocumentation',
	'supportedClass': 'http://www.w3.org/ns/hydra/core#supportedClass',
	'Collection': 'http://www.w3.org/ns/hydra/core#Collection',
	'Class': 'http://www.w3.org/ns/hydra/core#Class',
	'supportedProperty': 'http://www.w3.org/ns/hydra/core#supportedProperty',
	'property': 'http://www.w3.org/ns/hydra/core#property',
	'supportedOperation': 'http://www.w3.org/ns/hydra/core#supportedOperation',
	'readonly': 'http://www.w3.org/ns/hydra/core#readonly',
	'writeonly': 'http://www.w3.org/ns/hydra/core#writeonly',
	'method': 'http://www.w3.org/ns/hydra/core#method',
	'returns': 'http://www.w3.org/ns/hydra/core#returns',
	'expects': 'http://www.w3.org/ns/hydra/core#expects',
	'Resource': 'http://www.w3.org/ns/hydra/core#Resource'
}

rdfs = {
	'label': 'http://www.w3.org/2000/01/rdf-schema#label',
	'range': 'http://www.w3.org/2000/01/rdf-schema#range'
}

scalar_types = {
	'http://www.w3.org/2001/XMLSchema#string': 'String',
	'http://www.w3.org/2001/XMLSchema#boolean': 'boolean',
	'http://www.w3.org/2001/XMLSchema#dateTime': 'java.util.Date',
	'http://www.w3.org/2002/07/owl#Nothing': 'void'
}

prefix_mapping = {
	hydra['Collection']: 'java.util.Collection'
}

def main():
	doc = json.load(sys.stdin)
	for e in doc:
		if ('@type' not in e 
				or '@id' not in e
				or hydra['supportedClass'] not in e
				or hydra['ApiDocumentation'] not in e['@type']):
			continue
		prefix_mapping[e['@id']] = ''
		for c in e[hydra['supportedClass']]:
			if '@type' not in c:
				continue
			if hydra['Class'] in c['@type']:
				generate_class(c)

def generate_class(c):
	if rdfs['label'] not in c:
		return
	print('public interface {} {{'.format(c[rdfs['label']][0]['@value']))
	if hydra['supportedProperty'] in c:
		for sp in c[hydra['supportedProperty']]:
			if hydra['property'] not in sp:
				continue
			p = sp[hydra['property']][0]
			if rdfs['label'] not in p:
				continue
			label = p[rdfs['label']][0]['@value']
			label = ''.join([ l.capitalize() for l in label.split('_') ])
			prop_type = replace_prefix(p[rdfs['range']][0]['@id'])
			if prop_type in scalar_types: prop_type = scalar_types[prop_type]
			read_only = hydra['readonly'] in sp and sp[hydra['readonly']][0]['@value']
			write_only = hydra['writeonly'] in sp and sp[hydra['writeonly']][0]['@value']
			if hydra['supportedOperation'] in p and p[hydra['supportedOperation']]:
				for so in p[hydra['supportedOperation']]:
					method_name = so[hydra['method']][0]['@value']
					expects = [ replace_prefix(exp['@id']) for exp in so[hydra['expects']] ] if hydra['expects'] in so else []
					returns = [ replace_prefix(exp['@id']) for exp in so[hydra['returns']] ] if hydra['returns'] in so else []
					generate_method(label, prop_type, method_name, expects, returns)
			else:
				generate_property(label, prop_type, read_only, write_only)
	# TODO: to reason about the best place for crud operations
	# if hydra['supportedOperation'] in c:
	# 	print([o['@id'] for o in c[hydra['supportedOperation']]])
	print('}')

def replace_prefix(prop_type):
	result = prop_type
	for prefix in prefix_mapping.keys():
		if result.startswith(prefix):
			result = result.replace(prefix, prefix_mapping[prefix])
			if result.startswith('#') or result.startswith('/'):
				result = result[1:len(result)]
	return result

def generate_property(label, prop_type, read_only, write_only):
	if not write_only: print('    {} get{}()'.format(prop_type, label))
	if not read_only: print('    void set{}({} {})'.format(label, prop_type, label[0].lower() + label[1:len(label)]))

def generate_method(label, prop_type, method_name, expects, returns):
	args = ', '.join([ e + ' '+ e[0].lower() + e[1:len(e)] for e in expects ])
	if 'GET' == method_name:
		print('    {} get{}({})'.format(returns[0], label, args))
	elif 'PUT' == method_name:
		print('    {} set{}({})'.format(returns[0], label, args))
	elif 'POST' == method_name and prop_type == prefix_mapping[hydra['Collection']]:
	 	print('    {} addTo{}({})'.format(returns[0], label, args))
	elif 'POST' == method_name and prop_type == hydra['Resource']:
		print('    {} {}({})'.format(returns[0], label, args))
	else:
		raise Exception('Operation not supported:', label, prop_type, expects, returns, method_name)

if __name__ == '__main__':
	main()