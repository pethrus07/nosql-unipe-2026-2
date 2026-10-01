# Bancos de Dados NoSQL, UNIPÊ 2026.2

Atividades da disciplina *Implementação e Gerenciamento de Bancos de Dados
NoSQL* (cód. 12865), Prof. Me. Ricardo Roberto de Lima.

Aluno: Pedro Oliveira

## Atividades

| # | Banco | O que foi feito | Entregáveis |
|---|---|---|---|
| [1](atividade1-mongodb/) | MongoDB | importação do dataset, inserção e 8 consultas | 2 prints e 2 arquivos de texto |
| [2](atividade2-riak/) | Riak | 6 objetos chave-valor em 3 buckets via HTTP | 2 prints |
| [3](atividade3-cassandra/) | Cassandra | keyspace, tabela e CRUD em CQL | 3 prints |
| [4](atividade4-neo4j/) | Neo4j | dois grafos, consultas Cypher e caminho mais curto | 5 prints e 1 arquivo de texto |
| [5](atividade5-dissertacao/) | | dissertação sobre a prova da PF 2018 | DOCX |

## Desafio Integrador

[GeoLog](desafio-geolog/) é uma plataforma de telemetria de frota com
persistência poliglota: SQLite para o cadastro, MongoDB com índice `2dsphere`
para a telemetria e Streamlit para a interface. Feito individualmente.

Entregáveis: [`geolog.py`](desafio-geolog/geolog.py) e o
[relatório técnico em PDF](desafio-geolog/GeoLog-Relatorio-Tecnico.pdf).

## Sobre os prints

Os prints são de execução real. Os de terminal saíram de um console rodando os
comandos, e os grafos da Atividade 4 vieram do Neo4j Browser com a consulta
aberta. Nenhuma imagem foi montada.

## Ambiente

As atividades pedem a máquina virtual distribuída em sala. Aqui os bancos
rodaram em contêiner, com os mesmos comandos e as mesmas versões. Muda só a
forma de conectar.

```bash
# MongoDB, usado na Atividade 1 e no GeoLog
docker compose -f infra/docker-compose.yml up -d

# Riak, Cassandra, Neo4j e Redis
docker compose -f infra/docker-compose.atividades.yml up -d
```

| Banco | Imagem | Porta |
|---|---|---|
| MongoDB | `mongo:7` | 27017 |
| Riak KV | `basho/riak-kv` | 8098 |
| Cassandra | `cassandra:5` | 9042 |
| Neo4j | `neo4j:5` | 7474 e 7687 |
| Redis | `redis:7-alpine` | 6379 |

Cada atividade tem um README com o comando que foi usado, o resultado obtido e
as notas que explicam os números.

A base `restaurantes.json` da Atividade 1 não está aqui por causa do tamanho. É
o primer-dataset oficial do MongoDB, disponível em
[mongodb/docs-assets](https://github.com/mongodb/docs-assets/tree/primer-dataset).
