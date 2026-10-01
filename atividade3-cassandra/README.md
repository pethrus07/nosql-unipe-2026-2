# Atividade 3 — Cassandra (slides 98–100)

Keyspace `unipe`, tabela `cadastro`, seis registros; depois alterar, excluir e
consultar por cargo.

## Como reproduzir

```powershell
docker compose -f infra/docker-compose.atividades.yml up -d cassandra
# o Cassandra leva ~60 s para aceitar CQL; o healthcheck do compose avisa

docker exec -i unipe-cassandra cqlsh < atividades/atividade3-cassandra/atividade3.cql
```

Os prints foram gerados por `scripts/capturar-terminal.ps1`, que roda os
comandos num console de verdade e fotografa a janela.

## Entregáveis

| Arquivo | Etapa | O que mostra |
|---|---|---|
| `entrega/etapa1-keyspace-tabela-registros.png` | 1 | criação do keyspace e da tabela + os 6 registros |
| `entrega/etapa2a-update-e-delete.png` | 2 | Theo passa a funcionário, Afonso é excluído (6 → 5 linhas) |
| `entrega/etapa2b-buscar-por-cargo.png` | 2 | buscar professores e alunos — e o que o Cassandra exige para isso |

## Resultado

Depois da Etapa 2, com Afonso removido e Theo mudado de cargo:

| cargo | quem |
|---|---|
| professor | Thyago |
| aluno | Fernanda |
| funcionario | Leonardo, Sophia, **Theo** |

## O que a atividade ensina de verdade

### 1. O `WHERE` do `UPDATE` e do `DELETE` só aceita a chave primária

```sql
UPDATE cadastro SET cargo = 'funcionario'
  WHERE id = 04b57f0e-33df-11e5-a151-feff819cdc9f;   -- Theo
```

Não existe `WHERE nome = 'Theo'`. O Cassandra precisa saber **em qual partição
escrever** antes de escrever — e quem determina a partição é a chave. Por isso
a atividade dá os UUIDs prontos: sem eles não dá para fazer a Etapa 2.

### 2. `SELECT` por coluna comum é recusado pelo banco

Este é o ponto alto da atividade, e ele **falha de propósito**:

```sql
SELECT nome, cargo FROM cadastro WHERE cargo = 'professor';
```
```
InvalidRequest: Cannot execute this query as it might involve data filtering
and thus may have unpredictable performance. If you want to execute this query
despite the performance unpredictability, use ALLOW FILTERING
```

O Cassandra **se recusa a executar uma consulta cujo custo ele não consegue
prever**. Num cluster real, filtrar por uma coluna que não é chave significa
perguntar a todos os nós e juntar as respostas — custo que cresce com o
tamanho do cluster, não com o do resultado.

Compare com o comportamento de um banco relacional, que aceitaria a consulta e
faria um *full table scan* em silêncio. A diferença de filosofia é o conteúdo
da aula: **o Cassandra prefere recusar a mentir sobre o custo.**

Duas saídas, e elas não são equivalentes:

| | `ALLOW FILTERING` | Índice secundário |
|---|---|---|
| O que faz | manda executar assim mesmo | cria uma estrutura de busca por `cargo` |
| Custo | varre tudo, toda vez | consulta direcionada |
| Quando serve | exploração, base pequena | quando a consulta é recorrente |

E existe uma terceira, que é **a resposta idiomática do Cassandra**: não
consultar por coluna comum, e sim **modelar uma tabela por consulta**. Se
"listar por cargo" é uma pergunta frequente, cria-se `cadastro_por_cargo` com
`cargo` como chave de partição. É o que o material chama de *modelagem dirigida
pela consulta*: em Cassandra você não modela o dado e depois consulta — você
parte da consulta e modela para ela.

### 3. A ordem do `SELECT` não é a ordem de inserção

```
Leonardo | funcionario
Thyago   | professor
Afonso   | professor
Fernanda | aluno
Sophia   | funcionario
Theo     | aluno
```

Inseri na ordem Thyago, Afonso, Fernanda, Theo, Sophia, Leonardo — e saiu
diferente. As linhas voltam ordenadas pelo **token** da chave de partição, que
é o hash do `id`. Sem chave de clustering não existe ordenação previsível, e
`ORDER BY` em coluna arbitrária não é aceito.

## Ambiente

Cassandra **5.0.9** em container (`cassandra:5`), nó único, `SimpleStrategy`
com fator de replicação 1. Num cluster real seria `NetworkTopologyStrategy`.
O heap está limitado a 512 MB no compose — sem teto, o Cassandra reserva 1/4
da RAM da máquina para guardar seis linhas.
