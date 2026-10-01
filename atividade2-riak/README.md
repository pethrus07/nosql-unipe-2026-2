# Atividade 2: Riak

Slides 82 a 84. Inserir seis objetos chave-valor em três buckets via HTTP,
listar as chaves, depois alterar, mover e excluir.

## Como rodar

```powershell
docker compose -f infra/docker-compose.atividades.yml up -d riak

powershell -File atividade2-riak/etapa1-comandos.ps1
powershell -File atividade2-riak/etapa2-comandos.ps1
```

## Entregáveis

| Arquivo | Etapa |
|---|---|
| `entrega/etapa1-inserir-e-listar.png` | os 6 objetos inseridos, lidos de volta, e as chaves de cada bucket |
| `entrega/etapa2-alterar-mover-excluir.png` | Theo passa para 25, Leonardo muda de bucket, Afonso é excluído |

## Estado final

| bucket | chaves |
|---|---|
| professores | Thyago (35), Leonardo (15) |
| alunos | Fernanda (32), Theo (25) |
| funcionarios | Sophia (20) |

## A API

Riak não tem linguagem de consulta. Tudo é HTTP.

| Operação | Rota |
|---|---|
| gravar | `PUT /buckets/<bucket>/keys/<chave>` com o valor no corpo |
| ler | `GET /buckets/<bucket>/keys/<chave>` |
| apagar | `DELETE /buckets/<bucket>/keys/<chave>` |
| listar chaves | `GET /buckets/<bucket>/keys?keys=true` |

Não existe `WHERE`. Só se chega a um valor sabendo a chave.

## Notas

**Mover entre buckets são três operações, não uma.** O bucket faz parte do
endereço do objeto, então mudar Leonardo de funcionário para professor é ler,
gravar no destino e apagar na origem. Não há transação entre as três. Se o
processo parasse no meio, Leonardo existiria nos dois buckets ao mesmo tempo.

**A listagem de chaves demora a atualizar.** Logo depois de apagar Afonso, o
`GET` da chave dele já devolvia 404, mas a listagem ainda mostrava o nome. Uns
30 segundos depois a listagem ficou correta. A leitura por chave é consistente
na hora, a listagem não, porque ela varre as partições e o objeto apagado deixa
um marcador que leva um tempo para ser recolhido. Por isso o script da etapa 2
espera antes de listar.

**O banco aceita qualquer coisa como valor.** Na primeira versão do script eu
li a resposta sem olhar o código HTTP. Quando a chave não existia, o Riak
devolvia 404 com o corpo `not found`, e o script gravou o texto "not found"
como se fosse a idade. Nenhum erro apareceu. O `riak-helpers.ps1` passou a
devolver status e corpo separados, e a etapa 2 para se o status não for 2xx.

**Apagar e regravar a mesma chave na sequência não funciona.** O `DELETE` deixa
um marcador por cerca de 3 segundos que vence a escrita seguinte. A limpeza do
script espera 8 segundos antes de reinserir.

## Ambiente

Riak KV 2.1.7 em contêiner (`basho/riak-kv`), nó único. O projeto foi
descontinuado pela Basho e essa é a última imagem publicada.

No PowerShell, `curl` é apelido de `Invoke-WebRequest`. Para usar o curl de
verdade é preciso escrever `curl.exe`.
