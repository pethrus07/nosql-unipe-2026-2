English | [Português](README.pt-BR.md)

# NoSQL Databases, UNIPÊ 2026.2

Coursework for *Implementation and Management of NoSQL Databases* (course
code 12865), Computer Science at UNIPÊ (Brazil), 2026.2 term. Five
assignments (MongoDB, Riak, Cassandra, Neo4j and a short essay) and one
capstone challenge with polyglot persistence.

Status: completed (2026-10). Academic work, not maintained.

Author: Pedro Oliveira ([pethrus07](https://github.com/pethrus07)).

## Assignments

| # | Database | What was done | Deliverables |
|---|---|---|---|
| [1](atividade1-mongodb/) | MongoDB | dataset import, inserts and 8 queries | 2 screenshots and 2 text files |
| [2](atividade2-riak/) | Riak | 6 key-value objects in 3 buckets over HTTP | 2 screenshots |
| [3](atividade3-cassandra/) | Cassandra | keyspace, table and CRUD in CQL | 3 screenshots |
| [4](atividade4-neo4j/) | Neo4j | two graphs, Cypher queries and shortest path | 5 screenshots and 1 text file |
| [5](atividade5-dissertacao/) | | essay on the 2018 Federal Police exam | DOCX |

## Capstone challenge

[GeoLog](desafio-geolog/) is a fleet telemetry platform with polyglot
persistence: SQLite for the registry, MongoDB with a `2dsphere` index for
telemetry, and Streamlit for the interface. Done individually.

Deliverables: [`geolog.py`](desafio-geolog/geolog.py) and the
[technical report (PDF, Portuguese)](desafio-geolog/GeoLog-Relatorio-Tecnico.pdf).

## About the screenshots

The screenshots come from real runs. Terminal ones were taken from a console
running the commands, and the Assignment 4 graphs came from Neo4j Browser with
the query open. No image was edited together.

## How to run

The assignments ask for the virtual machine handed out in class. Here the
databases ran in containers, with the same commands and the same versions.
Only the way to connect changes.

```bash
# MongoDB, used in Assignment 1 and in GeoLog
docker compose -f infra/docker-compose.yml up -d

# Riak, Cassandra, Neo4j and Redis
docker compose -f infra/docker-compose.atividades.yml up -d

# GeoLog
cd desafio-geolog
pip install -r requirements.txt
streamlit run geolog.py
```

| Database | Image | Port |
|---|---|---|
| MongoDB | `mongo:7` | 27017 |
| Riak KV | `basho/riak-kv` | 8098 |
| Cassandra | `cassandra:5` | 9042 |
| Neo4j | `neo4j:5` | 7474 and 7687 |
| Redis | `redis:7-alpine` | 6379 |

Each assignment has its own README with the command used, the result and
notes on the numbers. Those inner READMEs are in Portuguese only.

There are no automated tests: each assignment is checked by the screenshot
and output file that were handed in.

The `restaurantes.json` dataset for Assignment 1 is not included because of
its size. It is MongoDB's official primer dataset, available at
[mongodb/docs-assets](https://github.com/mongodb/docs-assets/tree/primer-dataset).

## License

All rights reserved.
