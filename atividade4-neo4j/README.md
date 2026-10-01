# Atividade 4 — Neo4j (slides 145–152)

Dois grafos: a rede social hipotética (modelar, consultar, atualizar) e a rede
de sete pessoas para o caminho mais curto.

## Como reproduzir

```bash
docker compose -f infra/docker-compose.atividades.yml up -d neo4j
# Browser em http://localhost:7474 — usuário neo4j, senha unipe2026

cd atividades/atividade4-neo4j
docker exec -i unipe-neo4j cypher-shell -u neo4j -p unipe2026 < 01-criar-grafo-rede-social.cypher
docker exec -i unipe-neo4j cypher-shell -u neo4j -p unipe2026 < 02-consultas.cypher
docker exec -i unipe-neo4j cypher-shell -u neo4j -p unipe2026 < 03-atualizar-grafo.cypher
docker exec -i unipe-neo4j cypher-shell -u neo4j -p unipe2026 < 04-grafo-caminho-mais-curto.cypher
```

Os prints do grafo saem de `scripts/capturar-grafo-neo4j.mjs`, que dirige o
Neo4j Browser com Playwright — o grafo desenhado só existe lá dentro.

## Entregáveis

| Arquivo | O que é |
|---|---|
| `entrega/consultas-neo4j.txt` | **o entregável principal** — todas as consultas com seus resultados |
| `entrega/grafo-01-rede-social-inicial.png` | o grafo do slide 146 recém-modelado |
| `entrega/grafo-02-rede-social-atualizado.png` | depois das mudanças do slide 149 |
| `entrega/grafo-03-rede-7-pessoas.png` | a rede de sete pessoas do slide 150 |
| `entrega/grafo-04-caminho-rafael-carol.png` | caminho mais curto Rafael ↔ Carol |
| `entrega/grafo-05-caminho-rafael-ana.png` | caminho mais curto Rafael ↔ Ana |

## Nota técnica: dois caminhos mais curtos, não um

O texto do slide 152 pede o caminho mais curto entre **Rafael e Ana**. As setas
de destaque do slide 150 marcam **Rafael e Carol**. Como os dois casos têm
valor didático diferente, entreguei os dois, com print de cada um.

| | saltos | caminhos concorrentes |
|---|---|---|
| Rafael → Ana | 2 | nenhum, só existe via Franciele |
| Rafael → Carol | 3 | sim: 3 saltos por Gabriel, 4 por Ana/Paulo, 4 por Renata |

Rafael → Ana é direto, o grafo só tem um caminho possível. Rafael → Carol é o
caso que justifica usar `shortestPath`, porque existem alternativas de
comprimentos diferentes e o algoritmo precisa escolher entre elas.

## O que a atividade ensina de verdade

### 1. O grafo tem integridade referencial — e o MongoDB não tem

Apagar Gabriel com `DELETE` simples **falha**:

```
Cannot delete node<0>, because it still has relationships.
```

O Neo4j se recusa a deixar um relacionamento apontando para o vazio. É
exatamente o oposto do que vimos na Atividade 1: lá, apagar uma sessão deixaria
968 voltas órfãs e o Mongo não reclamaria.

`DETACH DELETE` apaga o nó **e os relacionamentos dele**. E isso tem efeito em
cascata que o enunciado não menciona: junto com Gabriel foi embora o `CURTIU`
dele, e a foto "Meu cachorro" ficou com zero curtidas.

### 2. Propriedade ausente não é "coluna com NULL"

A consulta *"nome dos usuários que não possuam Estado Civil cadastrado"* só faz
sentido porque **Carol não tem a propriedade `estadoCivil`** — ela não existe no
nó, não é um campo vazio. Num relacional a coluna existiria em todas as linhas,
com `NULL` em algumas. Aqui, dois nós do mesmo label podem ter conjuntos de
propriedades diferentes, e `IS NULL` cobre os dois casos (ausente e nulo).

Mesma lição da Atividade 1 com `$exists`, em outra família de banco.

### 3. A direção da seta é a pergunta

*"A quantidade de pessoas que segue um usuário"*:

```cypher
MATCH (seguidor:Pessoa)-[:SEGUE]->(:Pessoa { nome: 'Carol' })
```

Invertendo a seta, a pergunta vira *"quantas pessoas Carol segue"* — outra
coisa. Neste grafo as duas dão 1 por coincidência, o que torna o erro
indetectável pelo resultado. Em grafo, a direção **é** semântica.

### 4. Caminho é sobre arestas, não sobre nós

`allShortestPaths` entre Rafael e Carol devolveu **o mesmo caminho 8 vezes**.
Não é bug: cada seta dupla do slide são **dois** relacionamentos dirigidos, e
o caminho percorre relacionamentos. Com 3 ligações no trajeto, são 2×2×2 = 8
combinações de arestas sobre a mesma sequência de pessoas.

Sem `DISTINCT` sobre a lista de nomes, a resposta parece dizer que existem 8
caminhos mínimos distintos. Existe **um**.

### 5. Modelar a seta dupla custa o dobro

O slide desenha `Segue` com seta dupla, que virou dois relacionamentos:
7 pessoas, 8 ligações, **16 relacionamentos**. O Neo4j não tem aresta não
dirigida — o que existe é consultar sem direção (`-[:SEGUE]-`, sem a ponta da
seta). Uma modelagem alternativa seria gravar um relacionamento só e sempre
consultar sem direção; a escolha muda a contagem de `count(r)` e o resultado da
consulta 3.

## Ambiente

Neo4j **5.26.30** Community em container (`neo4j:5`), heap limitado a 512 MB.
Usuário `neo4j`, senha `unipe2026` (definida no compose). O Browser fica em
<http://localhost:7474> e o Bolt em `7687`.

Nota: a Community Edition tem **um banco só**. Por isso os dois grafos da
atividade não convivem — cada `.cypher` começa com `MATCH (n) DETACH DELETE n`
e os prints foram tirados na ordem.
