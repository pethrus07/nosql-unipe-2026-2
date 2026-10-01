# Desafio Integrador: GeoLog

Plataforma de telemetria da frota da LogiTech Express, com persistência
poliglota. O cadastro de motoristas e veículos fica em SQLite, a telemetria com
coordenadas fica em MongoDB com índice `2dsphere`, e a interface é Streamlit.

Feito individualmente.

## Entregáveis

| Arquivo | O que é |
|---|---|
| `geolog.py` | a aplicação, em arquivo único, como o enunciado pede |
| `GeoLog-Relatorio-Tecnico.pdf` | relatório de 3 páginas com o diagrama de arquitetura |

## Como rodar

```bash
docker compose -f infra/docker-compose.yml up -d mongo

cd desafio-geolog
streamlit run geolog.py
```

Abre em http://localhost:8501. Na primeira execução os dois bancos são
semeados sozinhos e o `logitech.db` é criado na pasta.

## Os quatro módulos

| Módulo | O que faz | Onde está |
|---|---|---|
| 1 | cria o esquema do SQLite, popula os dois bancos e cria o índice `2dsphere` | seções 2 e 3 do arquivo |
| 2 | busca por raio com `$near` e mapa Folium | `veiculos_no_raio`, `desenhar_mapa` |
| 3 | cruza SQLite e MongoDB em memória | `visao_unificada` |
| 4 | indicadores e gráficos Plotly | `secao_dashboard` |
| bônus | gera telemetria nova e atualiza sem reiniciar | `simular_movimento` |

## Decisões de projeto

**O seed do enunciado virou o fim do histórico.** Os pontos que o enunciado dá
são tratados como a posição mais recente de cada veículo, e para trás são
gerados pontos anteriores. Sem isso o gráfico de variação de temperatura teria
um ponto por veículo e não mostraria variação nenhuma.

**A busca por raio tem dois passos.** Primeiro uma agregação devolve a posição
atual de cada veículo, depois a distância é medida contra essas posições. Com
uma busca direta o mesmo veículo apareceria várias vezes, em posições antigas,
porque a coleção guarda histórico.

**A posição atual é agregação, não `find`.** Filtrar a duplicata na aplicação
funcionaria com três veículos e quebraria com trezentos. A agregação resolve no
banco, que é onde o índice está.

**Coordenada é `[longitude, latitude]`.** É o contrário da forma como se fala.
Invertida, o ponto vai parar em outro hemisfério e nenhuma consulta acusa erro,
porque a coordenada continua sendo válida. O código monta a coordenada num
lugar só, para o engano não ter como se espalhar.

**`$maxDistance` é em metros.** O filtro do mapa está em quilômetros, então a
conversão acontece na chamada.

**O Streamlit reexecuta o script inteiro a cada clique.** A conexão com o banco
é criada uma vez por processo e as consultas ficam em cache com prazo de
validade, senão mover o raio no mapa abriria conexão nova toda vez.

**A média de temperatura entre veículos diz pouco.** Misturar carga refrigerada
com carga seca dá um número que não descreve nenhum veículo real. O indicador
ficou porque o enunciado pede, mas quem permite leitura honesta é o gráfico de
variação por veículo.

**"Frotas ativas" é ambíguo.** Pode ser veículo com telemetria recente ou
veículo com motorista ativo. Escolhi motorista ativo, que é o dado que existe
no cadastro, e o rótulo do indicador diz isso.

## Limites conhecidos

Não há verificação de que todo `veiculo_id` da telemetria exista no cadastro.
Um identificador órfão aparece no mapa e some da visão unificada, sem aviso. É
o preço de não ter chave estrangeira entre os dois bancos.

O cruzamento em memória atende o volume do estudo de caso. Em escala real a
visão unificada passaria a ser materializada em vez de recalculada a cada
leitura.

A telemetria é gerada por código e serve para demonstrar as consultas, não para
análise de verdade.

## Ambiente

Python 3.14, MongoDB 7 em contêiner, streamlit 1.62, pymongo 4.17, folium 0.20,
streamlit-folium 0.27, plotly 7.0, pandas 3.0.
