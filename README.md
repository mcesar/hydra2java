# hydra2java
Code generator that can be used to generate java interfaces from a Hydra-based JSON-LD document.

## Getting Started

- `$ easy_install PyLD rdflib rdflib-jsonld rdfextras`
- `$ chmod +x hydra2java-rdf.py`
- To test: `$ curl http://www.markus-lanthaler.com/hydra/api-demo/vocab | ./hydra2java-rdf.py`

- To test with Jersey:

```
$ cd <scr-path>

$ mvn archetype:generate -DarchetypeArtifactId=jersey-quickstart-grizzly2 \
-DarchetypeGroupId=org.glassfish.jersey.archetypes -DinteractiveMode=false \
-DgroupId=com.example -DartifactId=simple-service -Dpackage=com.example \
-DarchetypeVersion=2.17

$ cd <hydra2java-path>

$ curl http://www.markus-lanthaler.com/hydra/api-demo/vocab | \
./hydra2java-rdf.py -t class -p com.example \
-d <src-path>/simple-service/src/main/java/com/example

$ cd serializer

$ mvn clean install
(it may need to clone the hydra-java github repository and install it manually)
```
Add the following to the generated pom.xml, and also enable json support:
```
<dependency>
    <groupId>de.escalon.hypermedia</groupId>
    <artifactId>hydra-jsonld</artifactId>
    <version>[0.2.0-beta3-SNAPSHOT,)</version>
</dependency>
<dependency>
    <groupId>io.hydra2java</groupId>
    <artifactId>serializer</artifactId>
    <version>1.0-SNAPSHOT</version>
</dependency>
```
In Main.java, startServer method, add the following after instantiation of ResourceConfig:
```
rc.register(io.hydra2java.JsonLdProvider.class);
```
Add code to some generated classes, and proceed:
```
$ cd <scr-path>/simple-service

$ mvn clean test

$ mvn exec:java

(send some requests)
```

## Command-Line Options

- -f, --format=json-ld|..., default=json-ld
- -t, --type=class|interface, default=interface
- -p, --package=<package>, default=
- -d, --destination=<path>, default=
- -a, --no_annotations, default=False
- -m, --members=methods|properties|all, default=all
- -l, --delegate, default=False
- -s, --supplemental_annotations=<ann1>,<ann2>,..., default=
