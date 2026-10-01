# Atividade 3: Cassandra

Slides 98 a 100. Criar o keyspace `unipe` e a tabela `cadastro`, inserir seis
registros, depois alterar um cargo, excluir um registro e consultar por cargo.

## Como rodar

```powershell
docker compose -f infra/docker-compose.atividades.yml up -d cassandra

docker exec -i unipe-cassandra cqlsh < atividade3-cassandra/atividade3.cql
```

O Cassandra leva cerca de 60 segundos para aceitar CQL depois de subir. O
healthcheck do compose avisa quando está pronto.

## Entregáveis

| Arquivo | Etapa |
|---|---|
| `entrega/etapa1-keyspace-tabela-registros.png` | keyspace, tabela e os 6 registros |
| `entrega/etapa2a-update-e-delete.png` | Theo passa a funcionário, Afonso é excluído |
| `entrega/etapa2b-buscar-por-cargo.png` | busca por cargo, e o que o Cassandra exige para isso |

## Resultado

Depois da etapa 2:

| cargo | quem |
|---|---|
| professor | Thyago |
| aluno | Fernanda |
| funcionario | Leonardo, Sophia, Theo |

## Notas

**O `WHERE` do `UPDATE` e do `DELETE` só aceita a chave primária.** Não existe
`WHERE nome = 'Theo'`. O Cassandra precisa saber em qual partição vai escrever
antes de escrever, e quem determina a partição é a chave. É por isso que o
enunciado entrega os UUIDs prontos: sem eles não dá para fazer a etapa 2.

**O `SELECT` por coluna comum é recusado.** Esta consulta falha de propósito:

```sql
SELECT nome, cargo FROM cadastro WHERE cargo = 'professor';
```

```
InvalidRequest: Cannot execute this query as it might involve data filtering
and thus may have unpredictable performance. If you want to execute this query
despite the performance unpredictability, use ALLOW FILTERING
```

O banco se recusa a rodar uma consulta cujo custo ele não consegue prever. Num
cluster, filtrar por coluna que não é chave significa perguntar para todos os
nós e juntar as respostas. Um banco relacional aceitaria e faria a varredura
completa sem avisar.

Há três saídas. `ALLOW FILTERING` manda executar assim mesmo, varrendo tudo.
Um índice secundário cria uma estrutura de busca pelo campo. A terceira é a
forma idiomática do Cassandra: criar uma tabela por consulta, com `cargo` como
chave de partição. É a modelagem dirigida pela consulta, onde se parte da
pergunta e se monta a tabela para respondê-la.

**A ordem do resultado não é a ordem de inserção.** Inseri na ordem Thyago,
Afonso, Fernanda, Theo, Sophia, Leonardo, e o `SELECT` devolveu outra. As
linhas voltam ordenadas pelo token da chave de partição, que é o hash do `id`.
Sem coluna de clustering não existe ordem previsível.

## Ambiente

Cassandra 5.0.9 em contêiner (`cassandra:5`), nó único, `SimpleStrategy` com
fator de replicação 1. O heap está limitado a 512 MB no compose, porque sem
teto ele reserva um quarto da RAM da máquina para guardar seis linhas.
