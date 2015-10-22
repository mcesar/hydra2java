#!/usr/bin/python

# TODO
# - quando tiver IriTemplate e as opcoes forem sem anotacoes, usar o tipo Map

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
HX = Namespace('http://api.siop.gov.br/hydra-extension#')
OWL = Namespace('http://www.w3.org/2002/07/owl/')

prefix_mapping = {
    XSD.string: 'String',
    XSD.boolean: 'Boolean',
    XSD.dateTime: 'java.util.Date',
    XSD.decimal: 'java.math.BigDecimal',
    XSD.int: 'Integer',
    HYDRA.Collection: 'java.util.Collection',
    HYDRA.Resource: 'java.net.URI',
    OWL.Nothing: 'void'
}

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
    args = parser.parse_args()
    g = Graph().parse(sys.stdin, format=args.format)
    api = g.value(None, RDF.type, HYDRA.ApiDocumentation)
    ontology = g.value(None, RDF.type, OWL.Ontology)
    if api:
        objects = g.objects(api, HYDRA.supportedClass)
        prefix_mapping[api] = ''
        vocab = api
    if ontology:
        objects = g.subjects(RDFS.isDefinedBy, ontology)
        prefix_mapping[ontology] = ''
        vocab = ontology
    supplemental_annotations = []
    if args.supplemental_annotations:
        supplemental_annotations = args.supplemental_annotations.split(',')
    f = sys.stdout
    for c in objects:
        if api and not c.startswith(api):
            continue
        if ontology and not c.startswith(ontology):
            continue
        sufix = ''
        if args.members == "methods":
            sufix += 'Resource'
            if args.type == 'class':
                sufix += 'JaxRsImpl'
        if args.destination != '':
            f = file('{}{}{}{}.java'.format(args.destination, os.sep, class_label(c), sufix), 'w')
        generate_class(g, c, args.package, args.type, f, args.no_annotations, vocab,
                args.members, args.delegate, sufix, supplemental_annotations)
        if args.destination != '':
            f.close()

def generate_class(g, c, package, type_label, f, no_annotations, vocab,
        members, delegate, sufix, supplemental_annotations):
    cl = class_label(c) + sufix
    if package != '':
        f.write('package {};\n\n'.format(package))

    if not no_annotations:
        f.write('import javax.ws.rs.GET;\n')
        f.write('import javax.ws.rs.POST;\n')
        f.write('import javax.ws.rs.PUT;\n')
        f.write('import javax.ws.rs.DELETE;\n')
        f.write('import javax.ws.rs.Consumes;\n')
        f.write('import javax.ws.rs.Path;\n')
        f.write('import javax.ws.rs.Produces;\n')
        f.write('import javax.ws.rs.core.Context;\n')
        f.write('import javax.ws.rs.core.UriInfo;\n')
        f.write('import de.escalon.hypermedia.hydra.mapping.*;\n')
        f.write('import io.hydra2java.*;\n\n')
        f.write('@Vocab("{}")\n'.format(vocab))
        sps = g.objects(c, HYDRA.supportedProperty)
        terms = ''
        termTypes = ''
        for i, sp in enumerate(sps):
            p = g.value(sp, HYDRA.property)
            plabel =  camelCase(prop_label(p))
            if i > 0:
                terms += ',\n'
                termTypes += ',\n'
            terms += '@Term(define="{}",as="{}")'.format(plabel, p)
            termTypes += '@TermType(define="{}",type="@id")'.format(plabel)
        if list(g.objects(c, HYDRA.supportedOperation)):
            if len(terms) > 0:
                terms += ',\n'
                termTypes += ',\n'
            terms += '@Term(define="{}",as="{}")'.format(camelCase(class_label(c)), c)
            termTypes += '@TermType(define="{}",type="@id")'.format(camelCase(class_label(c)))
        if len(terms) > 0:
            f.write('@Terms({{\n{}\n}})\n'.format(terms))
            f.write('@TermTypes({{\n{}\n}})\n'.format(termTypes))
        f.write('@Expose("{}")\n'.format(class_label(c)))
        f.write('@Path("{}")\n'.format(class_label(c)))
        if type_label == 'class':
            f.write('@Resource({}.class)\n'.format(cl))
        for ann in supplemental_annotations:
            f.write('@' + ann + '\n')
    extends = ''
    sc = g.value(c,RDFS.subClassOf)
    if sc:
        extends = ' extends ' + replace_prefix(prefix_mapping, sc)

    f.write('public {} {}{} {{\n'.format(type_label, cl, extends))
    if delegate and type_label == 'class' and members == 'methods':
        f.write('\n    @javax.inject.Inject\n    private {} delegate;\n'.
                format(class_label(c) + 'Resource'))
    for sp in g.objects(c, HYDRA.supportedProperty):
        p = g.value(sp, HYDRA.property)
        plabel =  prop_label(p)
        r = g.value(p, RDFS.range)
        if r == None:
            raise Exception(cl + '>>>' + plabel + ' does not have a range' )
        prop_type = replace_prefix(prefix_mapping, r)
        if g.value(p, RDF.type) == RDF.List:
            prop_type = 'java.util.List<' + prop_type + '>'
        read_only = Literal(True).eq(g.value(sp, HYDRA.readonly))
        write_only = Literal(True).eq(g.value(sp, HYDRA.writeonly))
        ptype = g.value(p, RDF.type, None)
        if ptype in [HYDRA.Link, HYDRA.TemplatedLink]:
            if members in ("methods", "all"):
                operations = list(g.objects(p, HYDRA.supportedOperation))
                generate_methods(g, plabel, prop_type, operations,
                    [ plabel + '/' + str(o) for o in operations ], type_label, f, 
                    no_annotations, ptype, delegate, None)
        elif members in ("properties", "all"):
                generate_property(plabel, prop_type, read_only, write_only, type_label, f)
    if members in ("methods", "all"):
        operations = list(g.objects(c, HYDRA.supportedOperation))
        generate_methods(g, class_label(c), None,
                operations, [ str(o) for o in operations ], type_label, f, 
                no_annotations, HYDRA.Link, delegate, sufix)
    f.write('}\n')

def camelCase(s):
    return s[0].lower() + s[1:]

def prop_label(p):
    result = replace_prefix(prefix_mapping, p)
    if '/' in result:
        result = result.rpartition('/')[2]
    if '_' in result:
        result = ''.join([ l.capitalize() for l in result.split('_') ])
    else:
        result = result[0].upper() + result[1:len(result)]
    return result

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

def generate_property(label, prop_type, read_only, write_only, type_label, f):
    if not write_only:
        f.write('\n    {}{} get{}(){}\n'.format(access_level(type_label), prop_type, label,
            sufix(type_label, prop_type, False)))
    if not read_only:
        f.write('\n    {}void set{}({} {}){}\n'.format(access_level(type_label), label, prop_type,
            label[0].lower() + label[1:len(label)], sufix(type_label, 'void', False)))

def generate_methods(g, label, class_type, operations, paths, type_label, f, no_annotations, 
        ptype, delegate, sufix):
    no_operations = True
    for i, so in enumerate(operations):
        method_name = g.value(so, HYDRA.method)
        if ptype == HYDRA.TemplatedLink:
            if no_annotations:
                expects = ["java.util.Map<String,String>"]
            else:
                expects = ["@Context UriInfo"]
        else:
            expects = replace_prefix(prefix_mapping, g.objects(so, HYDRA.expects))
        returns = replace_prefix(prefix_mapping, g.objects(so, HYDRA.returns))
        returns = [ r+sufix if r == label else r for r in returns ]
        generate_method(label, class_type, method_name, expects, returns, paths[i], type_label,
            f, no_annotations, delegate, g.value(so, HX.IdGenerator))
        no_operations = False
    return no_operations

def generate_method(label, prop_type, method_name, expects, returns, path, type_label,
        f, no_annotations, delegate, id_generator):
    l = lambda x: list(list(x.rpartition('.')).pop().partition('<')[0].rpartition(' ')).pop()
    args = ', '.join([ e + ' '+ l(e)[0].lower() + l(e)[1:] for e in expects ])
    labelLower = label[0].lower() + label[1:]
    if id_generator:
        ig_str = '\n    @Id'
    else:
        ig_str = ''
    annotations = ''
    if not no_annotations:
        annotations = '    @{}\n    @Path("{}")\n    @Property("{}")\n    @{}("application/ld+json"){}\n'
    if Literal('GET').eq(method_name):
        if not no_annotations:
            annotations = annotations.format('GET', path, labelLower, 'Produces', ig_str)
        path_label = prop_label(path)
        path_label = path_label[0].lower() + path_label[1:]
        f.write('\n{}    {}{} {}({}){}\n'.format(
            annotations, access_level(type_label), returns[0], path_label, args,
            sufix(type_label, returns[0], delegate, path_label, expects)))
    elif Literal('PUT').eq(method_name):
        if not no_annotations:
            annotations = annotations.format('PUT', path, labelLower, 'Consumes', ig_str)
        f.write('\n{}    {}{} set{}({}){}\n'.format(annotations, access_level(type_label), 
            returns[0], label, args, sufix(type_label, returns[0], delegate, label)))
    elif Literal('POST').eq(method_name) and prop_type == prefix_mapping[HYDRA.Collection]:
        if not no_annotations:
            annotations = annotations.format('POST', path, labelLower, 'Consumes', ig_str)
        f.write('\n{}    {}{} addTo{}({}){}\n'.format(annotations, access_level(type_label), 
            returns[0], label, args, sufix(type_label, returns[0], delegate, label)))
    elif Literal('POST').eq(method_name) and prop_type == HYDRA.Resource:
        if not no_annotations:
            annotations = annotations.format('POST', path, labelLower, 'Produces', ig_str)
        f.write('\n{}    {}{} {}({}){}\n'.format(annotations, access_level(type_label), 
            returns[0], label, args, sufix(type_label, returns[0], delegate, label)))
    elif Literal('DELETE').eq(method_name):
        if not no_annotations:
            annotations = annotations.format('DELETE', path, labelLower, 'Produces', ig_str)
        f.write('\n{}    {}{} remove{}({}){}\n'.format(annotations, access_level(type_label), 
            returns[0], label, args, sufix(type_label, returns[0], delegate, label)))
    else:
        raise Exception('Operation not supported:', label, prop_type, expects, returns, method_name)

def sufix(type_label, returns, delegate, method_name='', expects=None):
    if type_label == 'class':
        if returns == 'void':
            if delegate:
                return ' {{\n        delegate.{}();\n    }}'.format(method_name)
            else:
                return ' {}'
        else:
            if delegate:
                delegate_arg = ''
                if expects != None and '@Context UriInfo' in expects:
                    delegate_arg = 'uriInfo.getQueryParameters()'
                return ' {{\n        return delegate.{}({});\n    }}'.format(method_name, delegate_arg)
            else:
                if returns == 'boolean':
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
