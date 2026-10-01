# Desafio Integrador — GeoLog

Plataforma de telemetria logística com **persistência poliglota**: SQLite para o
cadastro, MongoDB para a telemetria geoespacial, Streamlit como interface.

Vale **+1,0 ponto na AV1** (+0,5 no desafio bônus). Enunciado em
`../material/enunciados/Desafio-GeoLog-Poliglota.docx`.

## Como rodar

```bash
# 1. um MongoDB acessível (o do compose do repo serve)
docker compose -f ../infra/docker-compose.yml up -d mongo

# 2. a aplicação
cd desafio-geolog
../.venv/Scripts/python.exe -m streamlit run geolog.py
```

Abre em <http://localhost:8501>. Na primeira execução o banco é semeado
sozinho; o `logitech.db` é criado na pasta.

## Os quatro módulos, e onde cada um está no código

| Módulo | O que pede | Onde |
|---|---|---|
| 1 — Persistência e seed | SQLite com `motoristas`/`veiculos`, MongoDB com `telemetria` GeoJSON | seções 2 e 3 |
| 2 — Geoprocessamento | busca por raio com `$near`/`$geoWithin` + mapa Folium | `veiculos_no_raio`, `desenhar_mapa` |
| 3 — Visão unificada | cruzar SQLite × MongoDB em memória | `visao_unificada` |
| 4 — Dashboard | KPIs + gráficos Plotly | `secao_dashboard` |
| Bônus | botão que gera pontos novos e atualiza sem reiniciar | `simular_movimento` |

O arquivo é **um só**, como o enunciado exige, dividido em sete seções
numeradas.

---

## As decisões que precisam ser defendidas

### 1. Por que o seed do enunciado virou o *fim* do histórico

O enunciado sugere três leituras, uma por veículo. O Módulo 4 pede *"histórico
de variação de temperatura por veículo"* — e com uma leitura por veículo não
existe histórico: o gráfico seria um ponto.

A saída foi manter os três pontos dele como a leitura **mais recente** de cada
caminhão e gerar 12 horas de histórico para trás. Os números que ele espera
(4,2 °C / 65 km/h · −18,5 °C / 85 km/h · 22,0 °C / 0 km/h) continuam aparecendo
na tela, e o Módulo 4 passa a ter o que plotar.

### 2. Por que a busca por raio tem dois passos

```python
ids_atuais = [doc["_id"] for doc in posicoes_atuais(colecao)]
# ... $geoNear com query: {"_id": {"$in": ids_atuais}}
```

Rodar `$geoNear` direto na coleção inteira responderia **outra pergunta**:
*"quais leituras já aconteceram perto daqui"*. Um caminhão que passou pela base
há seis horas e hoje está do outro lado da cidade entraria no resultado — com a
posição de seis horas atrás. O mapa mostraria ele onde ele não está, e nada
acusaria o erro.

`$geoNear` precisa ser o primeiro estágio do pipeline, então a restrição entra
pelo parâmetro `query` dele, e não num `$match` posterior.

### 3. Por que `posicoes_atuais` é agregação e não `find()`

Esta é a decisão que o bônus cobra. Com o seed original, cada veículo tem uma
leitura só — um `find()` simples funcionaria. Depois do primeiro clique em
"Simular movimentação" passam a existir várias, e o `find()` devolveria todas,
ou uma qualquer.

Medido: após três cliques, 153 leituras no banco (51 por veículo) e a tabela
unificada continuou com **três linhas**, uma por caminhão, com os valores novos.

O pipeline é `$sort` → `$group` com `$first` → `$replaceRoot`. O `$first` só
devolve o mais recente **porque** o `$sort` veio antes; sem ele, devolveria um
documento arbitrário — e plausível, que é o pior tipo de erro.

### 4. `sqlite3` em vez de SQLAlchemy

O enunciado permite os dois. Com `sqlite3` o `CREATE TABLE` e a `FOREIGN KEY`
ficam visíveis no código. Com ORM, ficariam atrás de classes — e numa arguição
isso vira ponto fraco.

Detalhe que quase todo mundo esquece: **o SQLite não valida chave estrangeira
por padrão**. Sem `PRAGMA foreign_keys = ON`, daria para cadastrar um veículo
apontando para um motorista inexistente — ou seja, o relacional perderia
exatamente a garantia que motivou escolher ele.

### 5. A ordem das coordenadas

GeoJSON é `[longitude, latitude]`. Folium é `[latitude, longitude]`. A inversão
está comentada em toda ocorrência no código, de propósito.

Se esquecer, o mapa **renderiza normalmente** e o caminhão aparece no Atlântico
Sul — porque latitude −34 e longitude −7 caem no oceano, perto da África.

Conferência feita: a distância que o `$geoNear` devolveu bate com uma haversine
calculada em Python **ao metro** (função `distancia_km`, que existe só para
isso).

### 6. `$maxDistance` é em metros

A interface pergunta em km. Errar o fator 1000 para menos não devolve nada — dá
para perceber. Errar para mais devolve a frota inteira, e **parece que
funcionou**.

### 7. Streamlit reexecuta o script inteiro a cada clique

Três consequências tratadas no código:

- o seed do SQLite usa `INSERT OR REPLACE` (idempotente); a carga do MongoDB só
  roda se a coleção estiver vazia
- o `MongoClient` está sob `@st.cache_resource`, senão cada interação abriria
  uma conexão nova
- o `st_folium` usa `returned_objects=[]`, senão arrastar o mapa dispararia uma
  reexecução completa

### 8. A média de temperatura não descreve nada

O KPI está no enunciado e por isso aparece. Mas a frota mistura carga congelada
(−18,5 °C), refrigerada (4,2 °C) e seca (22,0 °C): a média dá **2,5 °C**, que
não é a temperatura de caminhão nenhum. São três regimes somados, não uma
variação em torno de um valor.

A aplicação mostra o número **e** a ressalva, e o gráfico por veículo ao lado é
a leitura que de fato serve. Vale repetir isso no relatório.

### 9. "Total de frotas ativas" é ambíguo

Frota é o conjunto — "total de frotas" não faz sentido com uma transportadora
só. O campo `status` existe em **motoristas** (`Ativo` / `Em Descanso`), não em
veículos. Interpretei como **veículos cujo motorista está ativo** e rotulei o
KPI assim na tela, em vez de adivinhar em silêncio.

---

## O que ainda falta

- [ ] **Relatório técnico em PDF, até 3 páginas, com o diagrama de arquitetura
      poliglota.** É entregável tanto quanto o `.py` e costuma ser esquecido.
- [ ] **Definir o grupo** — o desafio é de 2 a 3 alunos.

## Ambiente verificado

MongoDB 7 em container, Python 3.14, Streamlit 1.62, pymongo 4.17, folium 0.20,
streamlit-folium 0.27.4, plotly 7.0, pandas 3.0.
