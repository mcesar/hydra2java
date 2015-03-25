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

(add code to some generated classes and enable json support on pom.xml)

$ cd <scr-path>/simple-service

$ mvn clean test

$ mvn exec:java

(send some requests)
```