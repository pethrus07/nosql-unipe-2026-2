# Atividade 2 — Riak (slides 82–84)

Seis objetos chave-valor em três buckets, via HTTP; depois alterar, mover,
excluir e listar.

## Como reproduzir

```powershell
docker compose -f infra/docker-compose.atividades.yml up -d riak
# o /ping responde em poucos segundos: curl.exe http://localhost:8098/ping

powershell -File atividades/atividade2-riak/etapa1-comandos.ps1
powershell -File atividades/atividade2-riak/etapa2-comandos.ps1
```

## Entregáveis

| Arquivo | Etapa |
|---|---|
| `entrega/etapa1-inserir-e-listar.png` | 1 — os 6 objetos inseridos, lidos de volta e as chaves de cada bucket |
| `entrega/etapa2-alterar-mover-excluir.png` | 2 — Theo para 25, Leonardo muda de bucket, Afonso excluído |

## Estado final

| bucket | chaves |
|---|---|
| professores | Thyago (35), **Leonardo (15)** |
| alunos | Fernanda (32), **Theo (25)** |
| funcionarios | Sophia (20) |

## A API é HTTP puro

| Operação | Verbo e rota |
|---|---|
| gravar | `PUT /buckets/<bucket>/keys/<chave>` com o valor no corpo |
| ler | `GET /buckets/<bucket>/keys/<chave>` |
| apagar | `DELETE /buckets/<bucket>/keys/<chave>` |
| listar chaves | `GET /buckets/<bucket>/keys?keys=true` |

Não há linguagem de consulta. Não há `WHERE`. O bucket é só um espaço de
nomes — **você só consegue chegar a um valor se souber a chave**. É o ponto do
vocabulário da ementa: *"por que não existe consulta por valor"*.

## O que a atividade ensina de verdade

### 1. Não existe "mover" — existe ler, gravar e apagar

*"Faça com que Leonardo deixe de ser um funcionário e passe a ser um professor"*
soa como um `UPDATE ... SET bucket = ...`. Não é. O bucket faz parte do
endereço do objeto, então mudar de bucket é **mudar a identidade**:

```
GET    funcionarios/Leonardo   -> 15
PUT    professores/Leonardo = 15
DELETE funcionarios/Leonardo
```

Três chamadas, **sem transação entre elas**. Se o processo morresse entre a
segunda e a terceira, Leonardo existiria nos dois buckets. Num relacional isso
seria um `UPDATE` atômico. É a troca que a família chave-valor faz: simplicidade
e velocidade extremas no acesso por chave, em troca de tudo o mais.

### 2. A listagem de chaves é eventualmente consistente — e isso dá para ver

O achado mais interessante da atividade. Logo depois de apagar Afonso:

| | |
|---|---|
| `GET professores/Afonso` | **404 not found** — imediato |
| `GET /keys?keys=true` | **ainda listava Afonso** |
| a mesma listagem ~30 s depois | correta |

A leitura por chave é consistente na hora; a **listagem** não, porque ela varre
as partições e o objeto apagado deixa um *tombstone* que só é recolhido depois.
Isso é consistência eventual acontecendo na prática, não no slide — e mostra
por que a própria documentação do Riak desaconselha listar chaves em produção:
é uma operação cara e sem garantia de exatidão no instante.

Por isso o script da Etapa 2 espera antes de listar.

### 3. Dois erros meus que valeram mais que o exercício

**Usar o corpo da resposta sem olhar o status.** A primeira versão fazia:

```powershell
$idade = curl.exe -s "$B/funcionarios/keys/Leonardo"
```

Quando a chave não existia, o Riak devolveu **404 com o corpo `not found`** — e
o script gravou a string `"not found"` como se fosse a idade. O banco aceitou
sem reclamar: em chave-valor o valor é opaco, qualquer byte serve. Um relacional
com a coluna `INTEGER` teria recusado.

A correção está em `riak-helpers.ps1`: `Ler()` devolve status e corpo separados,
e a Etapa 2 aborta se o status não for 2xx.

**Apagar e regravar a mesma chave no ato.** A limpeza do script apagava as
chaves e reinseria em seguida — e o `PUT` se perdia, porque o *tombstone* do
`DELETE` (≈3 s no `delete_mode` padrão) vence a escrita seguinte. Hoje a limpeza
espera 8 segundos.

## Ambiente

Riak KV **2.1.7** em container (`basho/riak-kv:latest`), nó único. O projeto foi
descontinuado pela Basho e esta é a última imagem publicada — ela ainda sobe e
responde normalmente.

Detalhe de PowerShell: **`curl` é apelido de `Invoke-WebRequest`**. Para usar o
curl de verdade é preciso escrever `curl.exe`.
