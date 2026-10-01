# Atividade 1 — MongoDB

Slides 64 a 69 do deck. Importar um dataset, inserir um documento e executar
oito consultas, quatro simples e quatro com operadores.

## Entregáveis

| Arquivo | Etapa |
|---|---|
| [entrega/etapa1-importacao.png](entrega/etapa1-importacao.png) | `mongoimport` criando `atividade1.restaurants` |
| [entrega/etapa2-insercao.png](entrega/etapa2-insercao.png) | inserção do documento do slide 66 |
| [entrega/etapa3-consultas.txt](entrega/etapa3-consultas.txt) | as 4 consultas simples, com comando e resultado |
| [entrega/etapa4-consultas-operadores.txt](entrega/etapa4-consultas-operadores.txt) | as 4 consultas com operadores |

O script da inserção está em [inserir-vella.js](inserir-vella.js).

## Como reproduzir

```bash
docker compose -f infra/docker-compose.yml up -d mongo

docker cp restaurantes.json nosql-unipe-mongo:/tmp/
docker exec nosql-unipe-mongo mongoimport \
  --db atividade1 --collection restaurants --file /tmp/restaurantes.json
docker exec -it nosql-unipe-mongo mongosh atividade1
```

## Resultados

| Consulta | Retorno |
|---|---|
| Todos os restaurantes | 25.360 |
| Bairro Manhattan | 10.260 |
| CEP 10022 | 485 |
| Com alguma nota B | 8.281 |
| `score` maior que 30 | 1.959 |
| `score` menor que 10 | 19.065 |
| Italiano **e** CEP 10075 | 16 |
| Italiano **ou** CEP 10075 | 1.154 |

## Notas técnicas

**O dataset.** A base usada é o *primer-dataset* oficial do MongoDB, com 25.359
restaurantes de Nova York. Ele é o que sustenta as oito consultas: os campos
`borough`, `cuisine`, `address.zipcode` e `grades[].grade` precisam existir, e o
primeiro documento dele é exatamente o que aparece no slide 66. Baixado de
`raw.githubusercontent.com/mongodb/docs-assets/primer-dataset`.

Vale conferir o formato antes de importar: se o arquivo começa com `{`, é JSON
Lines e o `mongoimport` lê direto; se começa com `[`, é um array e precisa de
`--jsonArray`.

**Tipo na comparação.** O CEP está gravado como texto. `{"address.zipcode": 10022}`
sem aspas devolve zero documentos, porque o MongoDB não converte tipo em
comparação de igualdade. É o tipo de erro que não gera mensagem nenhuma.

**Notação de ponto sobre array.** `{"grades.grade": "B"}` casa o documento se
**qualquer** elemento do array satisfizer a condição, que é o que a questão pede.
Para exigir que as duas condições caiam no mesmo elemento, seria `$elemMatch`.

**O documento duplicado.** O slide 66 manda inserir o restaurante "Vella", que já
existe na base. A inserção passa sem reclamar, porque só o `_id` tem unicidade
garantida, e a coleção fica com 25.360 documentos em vez de 25.359. Por isso a
consulta de italiano **e** CEP 10075 devolve 16 e não 15. Registrado aqui porque
o número só faz sentido com essa explicação.
