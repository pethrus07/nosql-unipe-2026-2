# Atividade 4: Neo4j

Slides 145 a 152. Dois grafos: a rede social do slide 146, que é modelada,
consultada e atualizada, e a rede de sete pessoas do slide 150, usada para o
caminho mais curto.

## Como rodar

```bash
docker compose -f infra/docker-compose.atividades.yml up -d neo4j

cd atividade4-neo4j
docker exec -i unipe-neo4j cypher-shell -u neo4j -p unipe2026 < 01-criar-grafo-rede-social.cypher
docker exec -i unipe-neo4j cypher-shell -u neo4j -p unipe2026 < 02-consultas.cypher
docker exec -i unipe-neo4j cypher-shell -u neo4j -p unipe2026 < 03-atualizar-grafo.cypher
docker exec -i unipe-neo4j cypher-shell -u neo4j -p unipe2026 < 04-grafo-caminho-mais-curto.cypher
```

O Browser fica em http://localhost:7474, usuário `neo4j`, senha `unipe2026`.

## Entregáveis

| Arquivo | O que é |
|---|---|
| `entrega/consultas-neo4j.txt` | todas as consultas com seus resultados |
| `entrega/grafo-01-rede-social-inicial.png` | o grafo do slide 146 |
| `entrega/grafo-02-rede-social-atualizado.png` | depois das mudanças do slide 149 |
| `entrega/grafo-03-rede-7-pessoas.png` | a rede de sete pessoas do slide 150 |
| `entrega/grafo-04-caminho-rafael-carol.png` | caminho mais curto entre Rafael e Carol |
| `entrega/grafo-05-caminho-rafael-ana.png` | caminho mais curto entre Rafael e Ana |

## Os dois caminhos mais curtos

O texto do slide 152 pede o caminho entre Rafael e Ana. As setas de destaque do
slide 150 marcam Rafael e Carol. Entreguei os dois, com print de cada um.

Rafael até Ana são 2 saltos e só existe um caminho, via Franciele. Rafael até
Carol são 3 saltos e existem alternativas de comprimentos diferentes, três por
Gabriel, quatro por Ana e Paulo, quatro por Renata. O segundo caso é o que
justifica usar `shortestPath`, porque o algoritmo precisa escolher.

## Notas

**O grafo tem integridade referencial.** Apagar Gabriel com `DELETE` simples
falha:

```
Cannot delete node<0>, because it still has relationships.
```

O Neo4j não deixa um relacionamento apontando para o vazio. `DETACH DELETE`
apaga o nó junto com os relacionamentos dele, e isso tem efeito em cascata que
o enunciado não comenta: junto com Gabriel foi o `CURTIU` dele, e a foto "Meu
cachorro" ficou com zero curtidas.

**Propriedade ausente não é campo nulo.** A consulta que pede os usuários sem
estado civil cadastrado funciona porque Carol simplesmente não tem a
propriedade `estadoCivil`. Ela não existe no nó. Num relacional a coluna
existiria em todas as linhas, com `NULL` em algumas. Dois nós do mesmo label
podem ter propriedades diferentes.

**A direção da seta muda a pergunta.** Contar quem segue Carol e contar quem
Carol segue são consultas diferentes, e neste grafo as duas dão 1 por
coincidência. Isso torna o erro invisível pelo resultado.

**`allShortestPaths` repetiu o mesmo caminho 8 vezes.** Cada seta dupla do
slide virou dois relacionamentos dirigidos, e o caminho percorre
relacionamentos, não nós. Com 3 ligações no trajeto são 2x2x2 combinações sobre
a mesma sequência de pessoas. Sem `DISTINCT` sobre a lista de nomes, a resposta
parece dizer que existem 8 caminhos mínimos. Existe um.

**A seta dupla custa o dobro.** 7 pessoas, 8 ligações, 16 relacionamentos. O
Neo4j não tem aresta sem direção. O que existe é consultar sem direção, usando
`-[:SEGUE]-`. Dava para gravar um relacionamento só e sempre consultar assim,
mas a contagem de `count(r)` mudaria.

## Ambiente

Neo4j 5.26.30 Community em contêiner (`neo4j:5`), heap limitado a 512 MB.

A Community Edition tem um banco só, então os dois grafos não convivem. Cada
arquivo `.cypher` começa limpando o banco, e os prints foram tirados na ordem.
