# -*- coding: utf-8 -*-
#!/usr/bin/env python
"""
Fill a Neo4j database with an edge stream where edges have timestamps.

Requires Python 2.7+

Usage
-------
python2.7 streamtoneo.py
"""
#    Copyright (C) 2013 by
#    Sébastien Heymann <sebastien.heymann@lip6.fr>
#    All rights reserved.
#    BSD license.
nodes = {}  #mapping between file node id and neo4j node id to avoid ensure that nodes are unique
node_property_list = ['name', 'lang', 'id']  #set up indexes in batch.properties
edge_property_list = ['timestamp']
node_cpt = 0
edge_cpt = -1
edge_iter_prev = None

def createNeo4jNode(f, properties):
        """Create a Neo4j node with a property dict"""
        global node_cpt
        node_cpt += 1
        s = '\t'.join([str(properties[p]) if p in properties else '' for p in node_property_list])
        f.write(s +'\n')
        return node_cpt

def createNeo4jRelationship(f, source, target, _type_, properties):
        """Create a Neo4j relationship"""
        global edge_cpt
        s = '\t'.join([str(properties[p]) if p in properties else '' for p in edge_property_list])
        f.write(str(source) + '\t' + str(target) + '\t' + _type_ + '\t' + s + '\n')
        edge_cpt += 1
        return edge_cpt

def createNeo4jIndexEntry(f, node, _type_):
        """Create a relationship between the Neo4j node and the Neo4j root node"""
        f.write('0\t' +str(node) + '\t' + _type_ +'\n')


def test():
        global nodes

        node_file = open('nodes.csv', 'w')
        node_file.write('name:string:users\tlang:string:repos\tid:int:edge_iter\n')
        rel_file = open('rels.csv', 'w')
        rel_file.write('start\tend\ttype\ttimestamp:int:edges\n')

        #the edge is from u to v
        u = 'A'
        v = 'B'
        properties = {'timestamp' : 1}

        #get or create node
        if u in nodes:
                source = nodes[u]
        else:
                source = createNeo4jNode(node_file, {'name' : u})
                nodes[u] = source
        
        #get or create node
        if v in nodes:
                target = nodes[v]
        else:
                target = createNeo4jNode(node_file, {'name' : v})
                nodes[v] = target

        #create edge
        edge = createNeo4jRelationship(rel_file, source, target, 'contribute', properties)

        node_file.close()
        rel_file.close()
        print "done"


def load(filePath):
        import csv, gzip
        from utils import CommentedFile
        global nodes, edge_iter_prev

        node_file = open('nodes.csv', 'w')
        node_file.write('name:string:users\tlang:string:repos\tid:int:edge_iter\n')
        rel_file = open('rels.csv', 'w')
        rel_file.write('start\tend\ttype\ttimestamp:int:edges\n')

        try:
                f = gzip.GzipFile(filePath, 'rb').read(1)  #raise exception if not a GZ
                f = gzip.open(filePath, 'rb')
        except IOError:
                f = open(filePath, 'r')
        reader = csv.reader(CommentedFile(f), delimiter=',')

        for row in reader:
                (u,v,r,l,t,d) = row   #source,target,repos,lang,type,date: specific to github edge stream
                v += '/' + r  #specific to github edge stream
                d = int(d)

                #get or create node
                if u in nodes:
                        source = nodes[u]
                else:
                        source = createNeo4jNode(node_file, {'name': u})
                        nodes[u] = source
        
                #get or create node
                if v in nodes:
                        target = nodes[v]
                else:
                        target = createNeo4jNode(node_file, {'name': v, 'lang': l})
                        nodes[v] = target

                #create edge
                properties = {'timestamp' : d}
                edge = createNeo4jRelationship(rel_file, source, target, t, properties)

                #create edge iterator in a separate subgraph
                edge_iter = createNeo4jNode(node_file, {'id': edge})
                if edge_iter_prev is not None:
                        createNeo4jRelationship(rel_file, edge_iter_prev, edge_iter, 'NEXT', {})
                edge_iter_prev = edge_iter

        node_file.close()
        rel_file.close()


if __name__ == "__main__":
        #import argparse
        #read command line arguments 
        # parser = argparse.ArgumentParser()
        # parser.add_argument("filePath", help="Path to the input file.")
        # parser.add_argument("-q", "--quiet", 
        #       help="No information on the standard output but critical errors.", 
        #       action="store_true")
        # args = parser.parse_args()

        #test()

        filePath = 'edgestream.csv.gz'
        load(filePath)
