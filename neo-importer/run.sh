#!/bin/sh
java -server -Xmx512m -jar batch-import-jar-with-dependencies.jar graph.db nodes.csv rels.csv

