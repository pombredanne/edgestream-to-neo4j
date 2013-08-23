# Edge stream storage in Neo4j

## Data model

An edge stream is a set of consecutive edges ordered by time of appearance. Each node may have a distinct set of properties. Each edge has a 'timestamp' property, and may have a specific type and a distinct set of properties.

## Data

Specifically, our data is a stream of events which happen on Github. We model 8 event types (e.g. CreateEvent, PushEvent, PullRequestEvent, IssueEvent) as a dynamic bipartite graph of users contributing to repositories at a given time.

The data contains more than 336,000 nodes and 2,200,000 edges and was captured during 18 weeks.

## Indexes

* relationships:edges: timestamp
* nodes:users: user name (optional)

## Queries

We provide indicative times of execution using Neo4j 1.9.2. The goal is to give a rough indication of the limits of our approach; it is not a rigorous benchmark. Query speed is given after a warm-up of 3 executions of the same query though the Web Admin.

**QUERY 1:** get the edge(s) at time '1342448901'

```
START r=relationship:edges(timestamp='1342448901')
RETURN r
```

Returned 2 rows. Query took **10ms**

*Two rows are returned because two edges have the same timestamp. This may be a problem that we have to deal with.**

**QUERY 2:** get the extremities of the edge(s) at time '1342448901'

```
START r=relationship:edges(timestamp='1342448901')
MATCH (n)-[r]->(m)
RETURN n,m
```

Returned 2 rows. Query took **13ms**

**QUERY 3:** get the nodes and edges over 24 hours 'from 1342448901 to 1342535301'

```
START r=relationship:edges('timestamp: [1342448901 TO 1342535301]')
MATCH (n)-[r]->(m)
RETURN r,n,m
```

Returned 23000 rows. Query took **1600ms**

**QUERY 4:** get the relationships of the node '197410' over 24 hours 'from 1342448901 to 1342535301'

```
START n=node(197410)
MATCH (n)-[r]-()
WHERE r.timestamp >= 1342448901 AND r.timestamp <= 1342535301
RETURN r
```

Returned 2 rows. Query took **17ms**

**QUERY 5:** get the next edge in the stream

```
START r=relationship:edges('timestamp: [1342448901 TO 9999999999]')
RETURN r
ORDER BY r.timestamp
SKIP 1
LIMIT 1
```

Returned 1 row. Query took **650ms**

**QUERY 6:** get 100 consecutive edges starting at a given time

```
START r=relationship:edges('timestamp: [1342448901 TO 9999999999]')
RETURN r
ORDER BY r.timestamp
LIMIT 100
```

Returned 100 row. Query took **650ms**

**QUERY 7:** get the previous edge in the stream

```
START r=relationship:edges('timestamp: [0 TO 1342448901]')
RETURN r
ORDER BY r.timestamp DESC
SKIP 1
LIMIT 1
```

Returned 1 row. Query took **75363ms**

**QUERY 8:** get the 100 previous edges in the stream
Not performed

The queries 4 to 6 have a problem when multiple edges have the same timestamp.
We can't reliably iterate over previous and next edges as we will get the edge of the same timestamp if it exists.
Moreover, querying the previous edges is deadly slow.

## Adding an 'edge iterator'

Our solution is to create a separate subgraph where nodes represent the edges and have the relationship ID as a property, and a relationship of type NEXT chains these nodes. This will help us to iterate in both directions of time from a given edge.

New index:

* nodes:edge_iter: id

### PROS
* we can iterate quickly over the edge stream
* we can iterate in both directions of time
* we can still represent nodes as Neo4j nodes and edges as Neo4j relationships.

### CONS
It comes with a large increase of the database size: for an edge stream of N distinct nodes and M distinct edges, the database contains N+M nodes and 2M-1 relationships. Thus instead of having N+M rows, we have N+3M-1 rows. The database now contains 2,620,000 nodes, 4,940,000 relationships and 4,550,000 properties with 9 relationship types.

**QUERY 4bis:** get the next edge in the stream after the edge of id '3'

```
START n=node:edge_iter(id='3')
MATCH (n)-[:NEXT]->(m)
RETURN m
```

where m.id is the relationship id.

Returned 1 row. Query took **10ms**

**QUERY 6bis:** get the 100 next edge in the stream after the edge of id '3'

```
START n=node:edge_iter(id='3')
MATCH (n)-[:NEXT*1..100]->(m)
RETURN m
```

where m.id is the relationship id.

Returned 100 rows. Query took **180ms**

**QUERY 7bis:** get the previous edge in the stream

```
START n=node:edge_iter(id='5')
MATCH (m)-[:NEXT]->(n)
RETURN m
```

where m.id is the relationship id.

Returned 1 row. Query took **10ms**

**QUERY 8bis:** get the 100 previous edges in the stream

```
START n=node:edge_iter(id='223')
MATCH (m)-[:NEXT*1..100]->(n)
RETURN m
```

where m.id is the relationship id.

Returned 100 rows. Query took **180ms**

*We see that we still have to look up the relationship in a second query to get its source and target nodes. Can we get the relationship directly?*

**QUERY 9:** get the previous edge in the stream, returning the relationship directly

```
START n=node:edge_iter(id='5'), r=relationship(*)
MATCH (m)-[:NEXT]->(n)
WHERE ID(r) = m.id
RETURN r
```

Returned 1 row. Query took **8900ms** (**47s** without warm-up)

*We can get the relationship directly but it is too slow.*

**QUERY 9bis:**

```
START n=node:edge_iter(id='5')
MATCH (m)-[:NEXT]->(n)
WITH m.id as id
START r=relationship(id)
RETURN r
```

*Doesn't work, question asked [here](http://stackoverflow.com/questions/18400881/neo4j-cypher-internal-parameters). It will be possible with Neo4j 2.0.*

**QUERY 10:** compute the degree of all edge extremities

```
START n=node:users('*:*')
MATCH n-[r]-()
WHERE HAS(r.timestamp)
RETURN ID(n), COUNT(r) ORDER BY COUNT(r) DESC
LIMIT 100
```


---
Compiled with Sublime Text and the plugins Markdown Editing, Markdown Preview and LiveReload following [this tutorial](http://www.perseosblog.com/en/posts/markdown-the-perfect-config-for-sublime-text-2/). See [Markdown-Cheatsheet](https://github.com/adam-p/markdown-here/wiki/Markdown-Cheatsheet).

---
### Related links

http://docs.neo4j.org/refcard/1.9/
https://github.com/ccattuto/neo4j-dynagraph/wiki/Representing-time-dependent-graphs-in-Neo4j