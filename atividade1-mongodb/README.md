# Atividade 1: MongoDB

Slides 64 a 69. Importar o dataset de restaurantes, inserir um documento e
executar oito consultas, quatro simples e quatro com operadores.

## Como rodar

```bash
docker compose -f infra/docker-compose.yml up -d mongo

docker cp restaurantes.json nosql-unipe-mongo:/tmp/
docker exec nosql-unipe-mongo mongoimport \
  --db atividade1 --collection restaurants --file /tmp/restaurantes.json
docker exec -it nosql-unipe-mongo mongosh atividade1
```

## Entregáveis

| Arquivo | Etapa |
|---|---|
| `entrega/etapa1-importacao.png` | o `mongoimport` criando `atividade1.restaurants` |
| `entrega/etapa2-insercao.png` | a inserção do documento do slide 66 |
| `entrega/etapa3-consultas.txt` | as 4 consultas simples, com comando e resultado |
| `entrega/etapa4-consultas-operadores.txt` | as 4 consultas com operadores |

O script da inserção está em `inserir-vella.js`.

## Resultados

| Consulta | Retorno |
|---|---|
| Todos os restaurantes | 25.360 |
| Bairro Manhattan | 10.260 |
| CEP 10022 | 485 |
| Com alguma nota B | 8.281 |
| `score` maior que 30 | 1.959 |
| `score` menor que 10 | 19.065 |
| Italiano e CEP 10075 | 16 |
| Italiano ou CEP 10075 | 1.154 |

## Notas

**A base.** É o primer-dataset oficial do MongoDB, com 25.359 restaurantes de
Nova York. Ele é o que sustenta as oito consultas, porque os campos `borough`,
`cuisine`, `address.zipcode` e `grades[].grade` precisam existir. O primeiro
documento dele é o mesmo que aparece no slide 66.

Antes de importar vale olhar o começo do arquivo. Se ele abre com `{`, é JSON
Lines e o `mongoimport` lê direto. Se abre com `[`, é um array e precisa de
`--jsonArray`.

**O tipo conta na comparação.** O CEP está gravado como texto. Escrever
`{"address.zipcode": 10022}` sem aspas devolve zero documentos, porque o
MongoDB não converte tipo em igualdade. Não aparece erro nenhum.

**Notação de ponto em array.** `{"grades.grade": "B"}` casa o documento se
qualquer elemento do array satisfizer a condição, que é o que a questão pede.
Para exigir que duas condições caiam no mesmo elemento seria `$elemMatch`.

**Por que a consulta de italiano e CEP 10075 devolve 16.** O slide 66 manda
inserir o restaurante "Vella", que já existe na base. A inserção passa sem
reclamar, porque só o `_id` tem unicidade garantida. A coleção fica com 25.360
documentos e a consulta devolve 16 em vez de 15.
