import sys
import types
import os

from rdflib import RDF, RDFS, XSD, Graph, URIRef, Literal, Namespace
from rdflib.parser import Parser
import rdfextras

rdfextras.registerplugins()

HYDRA = Namespace('http://www.w3.org/ns/hydra/core#')
HX = Namespace('http://api.siop.gov.br/hydra-extension#')
OWL = Namespace('http://www.w3.org/2002/07/owl#')

class Generator:
    def __init__(self, format='json-ld', type='interface', package='', destination='',
            no_annotations=False, members='all', delegate=False,
            supplemental_annotations='', collection_implementation=''):
        self.prefix_mapping = {
            XSD.string: 'String',
            XSD.boolean: 'Boolean',
            XSD.dateTime: 'java.util.Date',
            XSD.decimal: 'java.math.BigDecimal',
            XSD.int: 'Integer',
            HYDRA.Collection: 'java.util.Collection',
            HYDRA.Resource: 'java.net.URI',
            OWL.Nothing: 'void'
        }
        self.format = format
        self.type = type
        self.package = package
        self.destination = destination
        self.no_annotations = no_annotations
        self.members = members
        self.delegate = delegate
        self.supplemental_annotations = []
        if supplemental_annotations:
            self.supplemental_annotations = supplemental_annotations.split(',')
        if collection_implementation != '':
            self.prefix_mapping[HYDRA.Collection] = collection_implementation
        self.collection_implementation = collection_implementation

    def generate(self, input_file):
        g = Graph().parse(input_file, format=self.format)
        api = g.value(None, RDF.type, HYDRA.ApiDocumentation)
        ontology = g.value(None, RDF.type, OWL.Ontology)
        if api:
            objects = g.objects(api, HYDRA.supportedClass)
            self.prefix_mapping[api] = ''
            vocab = api
        if ontology:
            objects = g.subjects(RDFS.isDefinedBy, ontology)
            self.prefix_mapping[ontology] = ''
            vocab = ontology
        if not api and not ontology:
            raise Exception('Invalid input: neither api nor ontology found')
        f = sys.stdout
        for c in objects:
            if api and not c.startswith(api):
                continue
            if ontology and not c.startswith(ontology):
                continue
            sufix = ''
            if self.members == "methods":
                sufix += 'Resource'
                if self.type == 'class':
                    sufix += 'JaxRsImpl'
            if self.destination != '':
                f = file('{}{}{}{}.java'.\
                        format(self.destination, os.sep, self.replace_prefix(c), sufix), 'w')
            self.generate_class(g, c, f, vocab, sufix)
            if self.destination != '':
                f.close()

    def generate_class(self, g, c, f, vocab, sufix):
        cl = self.replace_prefix(c) + sufix
        if self.package != '':
            f.write('package %s;\n\n' % format(self.package))

        if not self.no_annotations:
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
                plabel = self.camelCase(self.prop_label(p))
                if i > 0:
                    terms += ',\n'
                    termTypes += ',\n'
                terms += '@Term(define="{}",as="{}")'.format(plabel, p)
                if g.value(p, RDF.type, None) in [HYDRA.Link, HYDRA.TemplatedLink]:
                    termTypes += '@TermType(define="{}",type="@id")'.format(plabel)
            if list(g.objects(c, HYDRA.supportedOperation)):
                if len(terms) > 0:
                    terms += ',\n'
                    termTypes += ',\n'
                terms += '@Term(define="{}",as="{}")'.\
                        format(self.camelCase(self.replace_prefix(c)), c)
                termTypes += '@TermType(define="{}",type="@id")'.\
                        format(self.camelCase(self.replace_prefix(c)))
            if len(terms) > 0:
                f.write('@Terms({{\n{}\n}})\n'.format(terms))
                f.write('@TermTypes({{\n{}\n}})\n'.format(termTypes))
            f.write('@Expose("{}")\n'.format(self.replace_prefix(c)))
            f.write('@Path("{}")\n'.format(self.replace_prefix(c)))
            if self.type == 'class':
                f.write('@Resource({}.class)\n'.format(cl))
            for ann in self.supplemental_annotations:
                f.write('@' + ann + '\n')
        extends = ''
        sc = g.value(c,RDFS.subClassOf)
        if sc:
            extends = ' extends ' + self.replace_prefix(sc)

        f.write('public {} {}{} {{\n'.format(self.type, cl, extends))
        if self.delegate and self.type == 'class' and self.members == 'methods':
            f.write('\n    @javax.inject.Inject\n    private {} delegate;\n'.
                    format(self.replace_prefix(c) + 'Resource'))
        for sp in g.objects(c, HYDRA.supportedProperty):
            p = g.value(sp, HYDRA.property)
            plabel = self.prop_label(p)
            r = g.value(p, RDFS.range)
            if r == None:
                raise Exception(cl + '>>>' + plabel + ' does not have a range' )
            prop_type = self.replace_prefix(r)
            if g.value(p, RDF.type) == RDF.List:
                prop_type = 'java.util.List<' + prop_type + '>'
            read_only = Literal(True).eq(g.value(sp, HYDRA.readonly))
            write_only = Literal(True).eq(g.value(sp, HYDRA.writeonly))
            ptype = g.value(p, RDF.type, None)
            if ptype in [HYDRA.Link, HYDRA.TemplatedLink]:
                if self.members in ("methods", "all"):
                    operations = list(g.objects(p, HYDRA.supportedOperation))
                    self.generate_methods(g, plabel, prop_type, operations,
                        [ plabel + '/' + str(o) for o in operations ], f,
                        ptype, None, vocab, self.replace_prefix(c))
            elif self.members in ("properties", "all"):
                self.generate_property(plabel, prop_type, read_only, write_only, f)
        if self.members in ("methods", "all"):
            operations = list(g.objects(c, HYDRA.supportedOperation))
            self.generate_methods(g, self.replace_prefix(c), None,
                    operations, [ str(o) for o in operations ], f,
                    HYDRA.Link, sufix, vocab, self.replace_prefix(c))
        f.write('}\n')

    def generate_property(self, label, prop_type, read_only, write_only, f):
        if not write_only:
            f.write('\n    {}{} get{}(){}\n'.format(self.access_level(), prop_type, label,
                self.sufix(prop_type)))
        if not read_only:
            f.write('\n    {}void set{}({} {}){}\n'.format(self.access_level(), label, prop_type,
                label[0].lower() + label[1:len(label)], self.sufix('void')))

    def generate_methods(self, g, label, class_type, operations, paths, f,
            ptype, sufix, vocab, class_label):
        no_operations = True
        for i, so in enumerate(operations):
            method_name = g.value(so, HYDRA.method)
            if ptype == HYDRA.TemplatedLink:
                if self.no_annotations:
                    expects = ["java.util.Map<String,String>"]
                else:
                    expects = ["@Context UriInfo"]
            else:
                expects = self.replace_prefix(g.objects(so, HYDRA.expects))
            returns = self.replace_prefix(g.objects(so, HYDRA.returns))
            if sufix == None:
                sufix = ''
            returns = [ r+sufix if r == label else r for r in returns ]
            self.generate_method(label, class_type, method_name, expects, returns, paths[i],
                f, g.value(so, HX.IdGenerator), vocab, class_label)
            no_operations = False
        return no_operations

    def generate_method(self, label, prop_type, method_name, expects, returns, path,
            f, id_generator, vocab, class_label):
        l = lambda x: list(list(x.rpartition('.')).pop().partition('<')[0].rpartition(' ')).pop()
        args = ', '.join([ e + ' '+ l(e)[0].lower() + l(e)[1:] for e in expects ])
        if id_generator:
            ig_str = '\n    @Id'
        else:
            ig_str = ''
        annotations = ''
        if not self.no_annotations:
            annotations = \
                '    @{}\n    @Path("{}")\n    @Property("{}")\n    @{}("application/ld+json"){}\n'
        if returns[0] == 'io.hydra2java.Collection':
            if not self.no_annotations:
                f.write('\n    @Vocab("%s")\n' % vocab)
                f.write('    @Expose("Collection")\n')
                f.write('    @Id')
            if self.type == 'class':
                collection_keyword = 'implements'
                if self.delegate and self.type == 'class' and self.members == 'methods':
                    collection_methods = [' { return delegate.getMembers(); }', 
                            ' { return delegate.getTemplate(); }', 
                            ' { return delegate.getMapping(); }']
                else:
                    collection_methods = [' { return null; }', ' { return null; }', ' { return null; }']
                collection_modifiers = 'private static'
            else:
                collection_keyword = 'extends'
                collection_methods = [';', ';', ';']
                collection_modifiers = 'public'
            f.write('\n    %s %s %s %s io.hydra2java.Collection {\n' % \
                    (collection_modifiers, self.type, self.prop_label(path), collection_keyword))
            if self.delegate and self.type == 'class' and self.members == 'methods':
                f.write('        @javax.inject.Inject\n        private {} delegate;\n'.
                        format(class_label + 'Resource.' + self.prop_label(path)))
            f.write('        public java.util.Collection<String> getMembers()%s\n' % collection_methods[0])
            f.write('        public String getTemplate()%s\n' % collection_methods[1])
            f.write('        public java.util.Map<String, String> getMapping()%s\n' % collection_methods[2])
            f.write('    }\n')
        if Literal('GET').eq(method_name):
            if not self.no_annotations:
                annotations = annotations.format('GET', path, self.camelCase(label), 'Produces', ig_str)
            path_label = self.prop_label(path)
            path_label = path_label[0].lower() + path_label[1:]
            f.write('\n{}    {}{} {}({}){}\n'.format(
                annotations, self.access_level(), returns[0], path_label, args,
                self.sufix(returns[0], path_label, expects)))
        elif Literal('PUT').eq(method_name):
            if not self.no_annotations:
                annotations = annotations.format('PUT', path, self.camelCase(label), 'Consumes', ig_str)
            f.write('\n{}    {}{} set{}({}){}\n'.format(annotations, self.access_level(),
                returns[0], label, args, self.sufix(returns[0], label)))
        elif Literal('POST').eq(method_name) and prop_type == self.prefix_mapping[HYDRA.Collection]:
            if not self.no_annotations:
                annotations = annotations.format('POST', path, self.camelCase(label), 'Consumes', ig_str)
            f.write('\n{}    {}{} addTo{}({}){}\n'.format(annotations, self.access_level(),
                returns[0], label, args, self.sufix(returns[0], label)))
        elif Literal('POST').eq(method_name) and prop_type == self.prefix_mapping[HYDRA.Resource]:
            if not self.no_annotations:
                annotations = annotations.format('POST', path, self.camelCase(label), 'Produces', ig_str)
            f.write('\n{}    {}{} {}({}){}\n'.format(annotations, self.access_level(),
                returns[0], label, args, self.sufix(returns[0], label)))
        elif Literal('DELETE').eq(method_name):
            if not self.no_annotations:
                annotations = annotations.format('DELETE', path, self.camelCase(label), 'Produces', ig_str)
            f.write('\n{}    {}{} remove{}({}){}\n'.format(annotations, self.access_level(),
                returns[0], label, args, self.sufix(returns[0], label)))
        else:
            raise Exception('Operation not supported:', label, prop_type, expects, returns, method_name)

    def camelCase(self, s):
        return s[0].lower() + s[1:]

    def prop_label(self, p):
        result = self.replace_prefix(p)
        if '/' in result:
            result = result.rpartition('/')[2]
        if '_' in result:
            result = ''.join([ l.capitalize() for l in result.split('_') ])
        else:
            result = result[0].upper() + result[1:len(result)]
        return result

    def replace_prefix(self, uri):
        if isinstance(uri, (list, types.GeneratorType)):
            result = []
            for each in uri:
                result.append(self.replace_prefix(each))
            return result
        result = uri
        for prefix in self.prefix_mapping.keys():
            if result.startswith(prefix):
                result = result.replace(prefix, self.prefix_mapping[prefix])
                if '#' in result:
                    result = result.rpartition('#')[2]
                if '/' in result:
                    result = result.rpartition('/')[2]
        return result

    def sufix(self, returns, method_name='', expects=None):
        if self.type == 'class':
            if returns == 'io.hydra2java.Collection':
                return ' { return new %s(); }' % (method_name[0].upper() + method_name[1:])
            elif returns == 'void':
                if self.delegate:
                    return ' {\n        delegate.%s();\n    }' % method_name
                else:
                    return ' {}'
            else:
                if self.delegate:
                    delegate_arg = ''
                    if expects != None and '@Context UriInfo' in expects:
                        delegate_arg = 'uriInfo.getQueryParameters()'
                    return ' {\n        return delegate.%s(%s);\n    }' \
                        % (method_name, delegate_arg)
                else:
                    if returns == 'boolean':
                        return ' { return false; }'
                    else:
                        return ' { return null; }'
        else:
            return ';'

    def access_level(self):
        if self.type == 'class':
            return 'public '
        else:
            return ''

