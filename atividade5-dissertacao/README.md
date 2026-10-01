# Atividade 5: Dissertação

Slides 162 e 163. Dissertação de até 30 linhas sobre a prova discursiva da
Polícia Federal de 2018, para Perito Criminal Federal, Área 3. Consulta
permitida, citação direta proibida.

## Entregável

`Atividade5-Dissertacao-PedroOliveira.docx`

O mesmo texto em formato corrido está em `texto-final.txt`.

## O que a prova pede

O texto motivador trata do volume de dados da Operação Lava Jato e do fato de
80% dos dados gerados hoje serem não estruturados, o que leva a problemas de
escalabilidade e custo.

| # | Pergunta | Valor |
|---|---|---|
| 1 | Definir banco de dados não relacional e citar duas vantagens sobre o modelo relacional | 3,40 |
| 2 | Discorrer sobre três modelos de gerenciamento de dados NoSQL | 6,00 |
| 3 | Comentar a vulnerabilidade dos bancos NoSQL a ataques de injeção NoSQL | 3,00 |

## Como o texto foi organizado

A questão 2 vale quase metade dos pontos de conteúdo, então ocupa quase metade
do espaço: 8 linhas para a primeira, 12 para a segunda e 9 para a terceira.

Os três modelos escolhidos foram documentos, chave-valor e família de colunas,
com uma menção ao modelo de grafos no fim. São os mesmos que foram usados nas
Atividades 1 a 4, em MongoDB, Riak, Cassandra e Neo4j.

A questão 3 trata de injeção NoSQL, que não é assunto do material da
disciplina. O conteúdo veio da documentação do MongoDB sobre validação de
entrada e dos operadores que permitem o ataque, principalmente `$ne`, `$gt`,
`$regex` e `$where`.

O documento tem 30 linhas e uma página, contadas no Word.
