"""
GeoLog - Plataforma de Telemetria Logistica com Persistencia Poliglota
======================================================================

Desafio Integrador - Implementacao e Gerenciamento de Bancos de Dados NoSQL
UNIPE 2026.2 - Prof. Me. Ricardo Roberto de Lima

Estudo de caso: a transportadora LogiTech Express opera uma frota de caminhoes
refrigerados. Os dados dela se dividem em dois regimes muito diferentes, e a
proposta do trabalho e usar um banco adequado para cada um:

    SQLite (logitech.db)          MongoDB (geolog_db)
    -------------------------     -----------------------------
    motoristas, veiculos          telemetria
    cadastro, muda pouco          chega o tempo todo
    exige integridade             formato varia com o sensor
    consulta relacional           consulta geoespacial

O criterio de corte nao e o tamanho do dado, e o FORMATO e o PADRAO DE ACESSO.
Um veiculo precisa apontar para um motorista que existe - isso o MongoDB nao
garante, e por isso o cadastro fica no relacional. Ja a telemetria chega em
alta frequencia com campos que mudam conforme o sensor; forcar isso numa
tabela de colunas fixas seria brigar com o dado.

O preco dessa escolha aparece no Modulo 3: nao existe JOIN entre bancos
diferentes. O cruzamento e feito em memoria, com pandas, e nao ha transacao
cobrindo os dois lados.


ARQUIVO UNICO
-------------
O enunciado pede "um unico arquivo .py". Para nao perder organizacao, o
arquivo esta dividido em sete secoes numeradas, cada uma com uma
responsabilidade so. A ordem e de baixo para cima: configuracao, persistencia,
consulta, cruzamento, apresentacao e, por ultimo, a aplicacao.


COMO RODAR
----------
    pip install streamlit pymongo pandas plotly folium streamlit-folium
    streamlit run geolog.py

Precisa de um MongoDB acessivel. Em container:
    docker run -d --name geolog-mongo -p 27017:27017 mongo:7
"""

from __future__ import annotations

import math
import os
import random
import sqlite3
from datetime import datetime, timedelta, timezone

import folium
import pandas as pd
import plotly.express as px
import streamlit as st
from pymongo import ASCENDING, GEOSPHERE, MongoClient
from streamlit_folium import st_folium


# =====================================================================
# 1. CONFIGURACAO
# =====================================================================
# Tudo que muda de maquina para maquina fica aqui, com valor padrao que
# funciona numa instalacao local. Assim o arquivo roda sem depender de .env.

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB = os.getenv("MONGO_DB_GEOLOG", "geolog_db")
COLECAO_TELEMETRIA = "telemetria"
SQLITE_ARQUIVO = os.getenv("SQLITE_GEOLOG", "logitech.db")

# Ponto de apoio padrao da transportadora: centro de Joao Pessoa.
# ATENCAO A ORDEM: GeoJSON e [longitude, latitude], nesta ordem, que e o
# inverso de como se fala ("estou na latitude tal"). O Folium, mais adiante,
# quer [latitude, longitude]. Trocar os dois e o erro classico de
# geoprocessamento: o mapa renderiza sem reclamar e o caminhao aparece no meio
# do Atlantico, porque -34 de latitude e -7 de longitude caem no oceano.
PONTO_APOIO = {"nome": "Base Joao Pessoa", "lon": -34.8770, "lat": -7.1195}

LIMITE_VELOCIDADE = 80          # km/h, definido pelo enunciado
RAIO_TERRA_KM = 6378.1          # usado pelo $centerSphere e pelo haversine

# Semente fixa: o seed precisa ser reproduzivel. Rodando duas vezes, ou noutra
# maquina, os numeros sao os mesmos - o que importa quando alguem vai conferir.
SEMENTE_ALEATORIA = 42


# =====================================================================
# 2. PERSISTENCIA RELACIONAL - SQLite
# =====================================================================
# Cadastro de motoristas e veiculos. Escolhi sqlite3 puro em vez de SQLAlchemy
# (o enunciado permite os dois) para o SQL ficar a vista: da para ler o
# CREATE TABLE e a chave estrangeira sem atravessar uma camada de ORM.

MOTORISTAS_SEED = [
    (1, "Carlos Andrade", "123456789", "Ativo"),
    (2, "Mariana Silva", "987654321", "Ativo"),
    (3, "Roberto Souza", "456789123", "Em Descanso"),
]

VEICULOS_SEED = [
    (101, "ABC-1A23", "Volvo FH 540", 1),
    (102, "XYZ-9876", "Scania R450", 2),
    (103, "KGB-4567", "Mercedes Actros", 3),
]


def conectar_sqlite() -> sqlite3.Connection:
    """Abre a conexao com o banco relacional.

    check_same_thread=False porque o Streamlit executa o script em threads
    diferentes a cada interacao; sem isso o sqlite3 recusa a conexao reusada.

    row_factory=sqlite3.Row faz cada linha responder por nome de coluna
    (linha["nome"]) em vez de so por posicao - o codigo fica legivel e nao
    quebra se a ordem das colunas mudar.
    """
    conexao = sqlite3.connect(SQLITE_ARQUIVO, check_same_thread=False)
    conexao.row_factory = sqlite3.Row
    # O SQLite NAO valida chave estrangeira por padrao. Sem esta linha, seria
    # possivel cadastrar um veiculo apontando para um motorista inexistente -
    # ou seja, o relacional perderia justamente a garantia que motivou
    # escolher ele para esta metade dos dados.
    conexao.execute("PRAGMA foreign_keys = ON")
    return conexao


def criar_esquema_sqlite(conexao: sqlite3.Connection) -> None:
    """Cria as duas tabelas do cadastro, se ainda nao existirem."""
    conexao.executescript(
        """
        CREATE TABLE IF NOT EXISTS motoristas (
            id     INTEGER PRIMARY KEY,
            nome   TEXT NOT NULL,
            cnh    TEXT NOT NULL UNIQUE,
            status TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS veiculos (
            id           INTEGER PRIMARY KEY,
            placa        TEXT NOT NULL UNIQUE,
            modelo       TEXT NOT NULL,
            motorista_id INTEGER NOT NULL,
            FOREIGN KEY (motorista_id) REFERENCES motoristas(id)
        );
        """
    )
    conexao.commit()


def semear_sqlite(conexao: sqlite3.Connection) -> None:
    """Carga inicial do cadastro.

    INSERT OR REPLACE deixa a operacao idempotente: rodar de novo reescreve as
    mesmas linhas em vez de estourar violacao de chave primaria. Isso importa
    porque o Streamlit reexecuta o script inteiro a cada clique do usuario -
    um seed que nao tolera repeticao quebraria na segunda interacao.
    """
    conexao.executemany(
        "INSERT OR REPLACE INTO motoristas (id, nome, cnh, status) VALUES (?, ?, ?, ?)",
        MOTORISTAS_SEED,
    )
    conexao.executemany(
        "INSERT OR REPLACE INTO veiculos (id, placa, modelo, motorista_id) VALUES (?, ?, ?, ?)",
        VEICULOS_SEED,
    )
    conexao.commit()


def ler_cadastro(conexao: sqlite3.Connection) -> pd.DataFrame:
    """Devolve veiculos e motoristas ja cruzados.

    Este JOIN e SQL de verdade, feito pelo banco - os dois lados estao no
    mesmo lugar. O cruzamento que precisa ser feito em memoria e o outro, com
    o MongoDB, e ele esta na secao 5.
    """
    consulta = """
        SELECT  v.id           AS veiculo_id,
                v.placa        AS placa,
                v.modelo       AS modelo,
                m.id           AS motorista_id,
                m.nome         AS motorista,
                m.cnh          AS cnh,
                m.status       AS status_motorista
        FROM veiculos v
        JOIN motoristas m ON m.id = v.motorista_id
        ORDER BY v.id
    """
    return pd.read_sql_query(consulta, conexao)


# =====================================================================
# 3. PERSISTENCIA DE DOCUMENTOS - MongoDB
# =====================================================================

# Estes tres pontos sao exatamente os do enunciado. Eles NAO sao a base
# inteira: entram como a leitura MAIS RECENTE de cada veiculo, e o historico
# anterior e gerado para tras a partir deles (ver gerar_telemetria).
#
# O motivo e pratico: o Modulo 4 pede "historico de variacao de temperatura
# por veiculo", e com uma leitura por veiculo nao existe historico - o grafico
# sairia com tres pontos soltos. Mantendo o seed do enunciado como estado
# atual, os numeros que ele espera continuam aparecendo na tela.
POSICOES_ATUAIS_SEED = [
    {
        "veiculo_id": 101,
        "coordenadas": [-34.873, -7.115],   # Joao Pessoa (Centro)
        "temperatura": 4.2,                  # carga refrigerada
        "velocidade": 65,
    },
    {
        "veiculo_id": 102,
        "coordenadas": [-34.832, -7.121],   # Cabo Branco
        "temperatura": -18.5,                # carga congelada
        "velocidade": 85,                    # acima do limite: gera alerta
    },
    {
        "veiculo_id": 103,
        "coordenadas": [-34.950, -7.150],   # Tibiri / BR-230
        "temperatura": 22.0,                 # carga seca, sem refrigeracao
        "velocidade": 0,                     # parado
    },
]

HORAS_DE_HISTORICO = 12
MINUTOS_ENTRE_LEITURAS = 15


@st.cache_resource
def conectar_mongo() -> MongoClient:
    """Abre o cliente do MongoDB.

    @st.cache_resource guarda a conexao entre as reexecucoes do Streamlit.
    Sem ele, cada clique do usuario abriria um MongoClient novo e os antigos
    ficariam pendurados - o pool de conexoes cresceria ate o servidor recusar.
    """
    cliente = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    cliente.admin.command("ping")   # falha aqui, e nao na primeira consulta
    return cliente


def colecao_telemetria():
    return conectar_mongo()[MONGO_DB][COLECAO_TELEMETRIA]


def criar_indices(colecao) -> None:
    """Cria o indice geoespacial 2dsphere. Exigido pelo enunciado.

    Nao e otimizacao: sem o indice, $near e $geoNear NAO RODAM - devolvem erro,
    e nao um resultado lento. E o unico indice do projeto cuja ausencia
    quebra funcionalidade em vez de so deixar devagar.

    2dsphere calcula sobre a esfera terrestre, e nao sobre um plano. Por isso
    as distancias saem em metros de superficie de verdade, e nao em "unidades
    de grau" - que nem teriam o mesmo tamanho em latitudes diferentes.

    create_index e idempotente: chamar a cada reexecucao do Streamlit nao
    recria nada, so confirma que existe.
    """
    colecao.create_index([("location", GEOSPHERE)], name="idx_location_2dsphere")
    # Este segundo indice e desempenho puro. Toda consulta do sistema ordena
    # por veiculo e por tempo (para achar a leitura mais recente de cada um),
    # e esse e exatamente o par de campos.
    colecao.create_index(
        [("veiculo_id", ASCENDING), ("timestamp", ASCENDING)],
        name="idx_veiculo_timestamp",
    )


def gerar_telemetria() -> list[dict]:
    """Monta o historico completo a ser inserido no MongoDB.

    A trajetoria e construida DE TRAS PARA A FRENTE: parte da posicao atual de
    cada veiculo (a do enunciado) e recua no tempo, deslocando o ponto um
    pouco a cada leitura. O ultimo documento gerado para cada veiculo e,
    portanto, identico ao seed original.

    A temperatura oscila em torno do regime do veiculo (congelado, refrigerado
    ou ambiente) e a velocidade varia dentro de uma faixa plausivel. Nao e
    simulacao fisica - e massa de teste com forma realista o suficiente para
    os graficos fazerem sentido.
    """
    random.seed(SEMENTE_ALEATORIA)
    agora = datetime.now(timezone.utc).replace(microsecond=0)
    leituras_por_veiculo = (HORAS_DE_HISTORICO * 60) // MINUTOS_ENTRE_LEITURAS

    documentos: list[dict] = []

    for atual in POSICOES_ATUAIS_SEED:
        lon, lat = atual["coordenadas"]
        temperatura = atual["temperatura"]
        velocidade = atual["velocidade"]

        # i = 0 e a leitura mais recente; i cresce indo para o passado
        for i in range(leituras_por_veiculo):
            instante = agora - timedelta(minutes=MINUTOS_ENTRE_LEITURAS * i)

            documentos.append(
                {
                    "veiculo_id": atual["veiculo_id"],
                    "location": {
                        "type": "Point",
                        "coordinates": [round(lon, 6), round(lat, 6)],
                    },
                    "temperatura": round(temperatura, 1),
                    "velocidade": int(velocidade),
                    # Gravado como datetime, e nao como string. O enunciado
                    # sugere "2026-09-11T10:00:00Z" entre aspas, mas texto nao
                    # se compara com $gte nem vira eixo temporal no Plotly sem
                    # conversao. O pymongo transforma datetime em BSON Date.
                    "timestamp": instante,
                }
            )

            # passo para a leitura anterior: recua o ponto e sacode os sensores
            if velocidade > 0:
                lon -= random.uniform(-0.004, 0.004)
                lat -= random.uniform(-0.004, 0.004)
            temperatura += random.uniform(-0.5, 0.5)
            velocidade = max(0, velocidade + random.randint(-8, 8))

    return documentos


def semear_telemetria(colecao) -> int:
    """Carga inicial da telemetria.

    Apaga e recarrega. Poderia ser incremental, mas para massa de teste a
    recarga completa e mais honesta: o estado do banco passa a ser funcao so
    do codigo, sem residuo de execucao anterior.

    Esta funcao NAO e chamada a cada reexecucao do Streamlit - so no primeiro
    carregamento (quando a colecao esta vazia) ou quando o usuario pede.
    """
    colecao.delete_many({})
    documentos = gerar_telemetria()
    colecao.insert_many(documentos)
    return len(documentos)


def preparar_bancos(recarregar: bool = False) -> dict:
    """Ponto unico de inicializacao: esquema, indices e carga.

    Roda a cada reexecucao do script, por isso tudo aqui dentro precisa ser
    idempotente. So a carga da telemetria e condicional, porque e a unica
    operacao cara.
    """
    conexao = conectar_sqlite()
    criar_esquema_sqlite(conexao)
    semear_sqlite(conexao)

    colecao = colecao_telemetria()
    criar_indices(colecao)

    inseridos = 0
    if recarregar or colecao.count_documents({}) == 0:
        inseridos = semear_telemetria(colecao)

    return {
        "conexao_sqlite": conexao,
        "colecao": colecao,
        "documentos_inseridos": inseridos,
        "total_telemetria": colecao.count_documents({}),
    }


# =====================================================================
# 4. CONSULTAS AO MONGODB
# =====================================================================

def posicoes_atuais(colecao) -> list[dict]:
    """A leitura mais recente de cada veiculo.

    Esta funcao e a peca central do sistema, e vale entender por que ela nao e
    um find() simples.

    A colecao guarda o HISTORICO: 48 leituras por veiculo. Um find() sem
    filtro devolveria as 144, e a pergunta "onde cada caminhao esta agora"
    exige exatamente uma por veiculo - a mais nova.

    O pipeline faz isso em tres estagios:
        $sort        ordena por tempo decrescente
        $group       agrupa por veiculo e guarda o PRIMEIRO de cada grupo,
                     que depois do sort e o mais recente
        $replaceRoot promove esse documento de volta para a raiz, para o
                     resultado ter o mesmo formato de um find()

    O $first so devolve o mais recente PORQUE o $sort veio antes. Sem o $sort,
    ele devolveria um documento arbitrario - e, o que e pior, um documento
    plausivel: nao daria erro, so responderia errado.
    """
    pipeline = [
        {"$sort": {"timestamp": -1}},
        {"$group": {"_id": "$veiculo_id", "ultimo": {"$first": "$$ROOT"}}},
        {"$replaceRoot": {"newRoot": "$ultimo"}},
        {"$sort": {"veiculo_id": 1}},
    ]
    return list(colecao.aggregate(pipeline))


def veiculos_no_raio(colecao, lon: float, lat: float, raio_km: float) -> list[dict]:
    """Veiculos que estao a ate `raio_km` do ponto informado, agora.

    Duas etapas, e a razao de serem duas e a parte importante:

    1. descobrir quais documentos representam a posicao ATUAL de cada veiculo
    2. perguntar quais desses estao dentro do raio

    Fazer so a etapa 2, rodando $geoNear direto na colecao inteira, responderia
    outra pergunta: "quais LEITURAS ja aconteceram perto daqui". Um caminhao
    que passou pela base ha seis horas e hoje esta do outro lado da cidade
    entraria no resultado, com a posicao de seis horas atras. O mapa mostraria
    ele onde ele nao esta - e nada acusaria o erro.

    $geoNear precisa ser o PRIMEIRO estagio do pipeline, entao a restricao aos
    documentos atuais entra pelo parametro `query` dele, e nao num $match
    depois.

    Detalhe de unidade: maxDistance e em METROS. A interface pergunta em km,
    por isso a multiplicacao por 1000. Errar esse fator para menos nao devolve
    nada (da para perceber); errar para mais devolve a frota inteira - e isso
    parece que funcionou.
    """
    ids_atuais = [doc["_id"] for doc in posicoes_atuais(colecao)]
    if not ids_atuais:
        return []

    pipeline = [
        {
            "$geoNear": {
                "near": {"type": "Point", "coordinates": [lon, lat]},
                "distanceField": "distancia_m",
                "maxDistance": raio_km * 1000,
                "query": {"_id": {"$in": ids_atuais}},
                # spherical=True manda calcular sobre a esfera. E o que faz o
                # indice 2dsphere ser usado e a distancia sair em metros.
                "spherical": True,
            }
        },
        {"$sort": {"distancia_m": 1}},
    ]
    return list(colecao.aggregate(pipeline))


def historico_telemetria(colecao) -> pd.DataFrame:
    """Todas as leituras, para os graficos do dashboard.

    Aqui o historico inteiro e desejado - e justamente o que o Modulo 4 pede.
    O DataFrame ja sai ordenado por veiculo e tempo, que e a forma que o
    Plotly espera para desenhar uma linha por veiculo.
    """
    documentos = list(
        colecao.find(
            {},
            {"_id": 0, "veiculo_id": 1, "temperatura": 1,
             "velocidade": 1, "timestamp": 1},
        ).sort([("veiculo_id", 1), ("timestamp", 1)])
    )
    return pd.DataFrame(documentos)


def rotas_recentes(colecao, horas: int = 3) -> pd.DataFrame:
    """Pontos percorridos por cada veiculo nas ultimas `horas`.

    Usado so para desenhar a linha da rota no mapa. O recorte por tempo existe
    porque o historico inteiro deixaria o mapa poluido - e porque "por onde
    passou agora ha pouco" e uma pergunta mais util que "por onde passou o dia
    todo".

    O filtro por $gte so funciona porque o timestamp foi gravado como data de
    verdade. Se estivesse como string, a comparacao seria lexicografica -
    funcionaria por acaso no formato ISO-8601, e quebraria em qualquer outro.
    """
    corte = datetime.now(timezone.utc) - timedelta(hours=horas)
    documentos = list(
        colecao.find(
            {"timestamp": {"$gte": corte}},
            {"_id": 0, "veiculo_id": 1, "location": 1, "timestamp": 1},
        ).sort([("veiculo_id", 1), ("timestamp", 1)])
    )
    if not documentos:
        return pd.DataFrame(columns=["veiculo_id", "lon", "lat", "timestamp"])

    return pd.DataFrame(
        {
            "veiculo_id": d["veiculo_id"],
            "lon": d["location"]["coordinates"][0],
            "lat": d["location"]["coordinates"][1],
            "timestamp": d["timestamp"],
        }
        for d in documentos
    )


def distancia_km(lon1: float, lat1: float, lon2: float, lat2: float) -> float:
    """Distancia em linha reta entre dois pontos, pela formula de haversine.

    O $geoNear ja devolve a distancia calculada pelo proprio MongoDB, entao
    esta funcao nao e usada no caminho principal. Ela existe para conferencia:
    permite comparar o numero que o banco deu com um calculado aqui, que e o
    tipo de verificacao que se faz quando um resultado geoespacial parece
    estranho.
    """
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2))
        * math.sin(dlon / 2) ** 2
    )
    return 2 * RAIO_TERRA_KM * math.asin(math.sqrt(a))


# =====================================================================
# 5. JOIN POLIGLOTA - o cruzamento em memoria
# =====================================================================

def visao_unificada(conexao: sqlite3.Connection, colecao) -> pd.DataFrame:
    """Cruza o cadastro do SQLite com a ultima telemetria do MongoDB.

    Este e o Modulo 3 do enunciado, e e o ponto onde o preco da persistencia
    poliglota fica visivel: NAO EXISTE JOIN entre bancos diferentes. Cada lado
    e consultado no seu proprio banco, com a linguagem dele, e o cruzamento
    acontece aqui, em memoria, com pandas.

    A cadeia tem dois saltos, nao um:

        telemetria.veiculo_id  ->  veiculos.id  ->  motoristas.id
              (MongoDB)              (SQLite)         (SQLite)

    O segundo salto e SQL de verdade, feito pelo banco em ler_cadastro(); so o
    primeiro precisa ser feito na aplicacao.

    O que se perde: nao ha transacao cobrindo os dois lados, e nada garante que
    todo veiculo_id vindo do MongoDB exista na tabela de veiculos. Por isso o
    merge e `left` a partir do cadastro - assim um veiculo sem telemetria
    aparece na tabela com os campos vazios, em vez de sumir em silencio.
    """
    cadastro = ler_cadastro(conexao)
    atuais = pd.DataFrame(posicoes_atuais(colecao))

    if atuais.empty:
        return cadastro

    atuais = atuais[["veiculo_id", "temperatura", "velocidade", "location", "timestamp"]].copy()
    # location e um dicionario GeoJSON; a tabela precisa de texto legivel
    atuais["coordenadas"] = atuais["location"].apply(
        lambda loc: f"{loc['coordinates'][1]:.4f}, {loc['coordinates'][0]:.4f}"
    )
    atuais = atuais.drop(columns=["location"])

    unificada = cadastro.merge(atuais, on="veiculo_id", how="left")
    unificada["acima_do_limite"] = unificada["velocidade"] > LIMITE_VELOCIDADE

    return unificada.rename(
        columns={
            "motorista": "Motorista",
            "placa": "Placa",
            "modelo": "Modelo",
            "status_motorista": "Status",
            "temperatura": "Ultima Temperatura (C)",
            "velocidade": "Velocidade (km/h)",
            "coordenadas": "Coordenadas (lat, lon)",
            "timestamp": "Leitura em",
        }
    )


# =====================================================================
# 6. APRESENTACAO - mapa, indicadores e graficos
# =====================================================================

def classificar_veiculo(velocidade: float, temperatura: float) -> tuple[str, str]:
    """Cor e motivo do marcador no mapa.

    A prioridade importa: velocidade acima do limite e alerta operacional e
    vence qualquer outra classificacao. Carga congelada nao e problema - e o
    regime normal de quem transporta congelado.
    """
    if velocidade > LIMITE_VELOCIDADE:
        return "red", f"velocidade {velocidade:.0f} km/h acima do limite"
    if temperatura < 0:
        return "blue", "carga congelada"
    if temperatura <= 10:
        return "green", "carga refrigerada"
    return "orange", "carga seca / ambiente"


def desenhar_mapa(ponto: dict, raio_km: float, veiculos: list[dict],
                  rotas: pd.DataFrame | None = None) -> folium.Map:
    """Monta o mapa com a base, a area de busca e os veiculos.

    ATENCAO A ORDEM DAS COORDENADAS. O MongoDB guarda GeoJSON, que e
    [longitude, latitude]. O Folium recebe [latitude, longitude]. A inversao
    acontece aqui, em todo ponto que vai para o mapa - e esta comentada em
    cada ocorrencia de proposito, porque e o erro que nao da mensagem: o mapa
    desenha normalmente, so que no lugar errado do planeta.
    """
    mapa = folium.Map(
        location=[ponto["lat"], ponto["lon"]],   # Folium: [lat, lon]
        zoom_start=12,
        tiles="OpenStreetMap",
    )

    # A area de busca, desenhada com o mesmo raio usado na consulta. Serve de
    # conferencia visual: se um marcador aparecer fora do circulo, ou o raio
    # ou a consulta esta errado.
    folium.Circle(
        location=[ponto["lat"], ponto["lon"]],
        radius=raio_km * 1000,                   # Folium quer metros, como o Mongo
        color="#2b6cb0",
        weight=2,
        fill=True,
        fill_opacity=0.08,
        popup=f"Raio de busca: {raio_km:g} km",
    ).add_to(mapa)

    folium.Marker(
        location=[ponto["lat"], ponto["lon"]],
        tooltip=ponto["nome"],
        icon=folium.Icon(color="darkblue", icon="home", prefix="fa"),
    ).add_to(mapa)

    # Rota percorrida: uma linha ligando as leituras de cada veiculo. O
    # enunciado pede "a rota OU a localizacao"; como o historico existe, dá
    # para mostrar as duas coisas.
    if rotas is not None and not rotas.empty:
        for veiculo_id, trecho in rotas.groupby("veiculo_id"):
            pontos = [
                [linha["lat"], linha["lon"]]      # de novo: [lat, lon]
                for _, linha in trecho.iterrows()
            ]
            folium.PolyLine(
                pontos, weight=2, opacity=0.5, color="#718096",
                tooltip=f"Rota do veiculo {veiculo_id}",
            ).add_to(mapa)

    for veiculo in veiculos:
        lon, lat = veiculo["location"]["coordinates"]     # GeoJSON: [lon, lat]
        cor, motivo = classificar_veiculo(veiculo["velocidade"], veiculo["temperatura"])
        distancia = veiculo.get("distancia_m", 0) / 1000

        popup = folium.Popup(
            f"<b>Veiculo {veiculo['veiculo_id']}</b><br>"
            f"Temperatura: {veiculo['temperatura']} C<br>"
            f"Velocidade: {veiculo['velocidade']} km/h<br>"
            f"Distancia da base: {distancia:.2f} km<br>"
            f"<i>{motivo}</i>",
            max_width=260,
        )
        folium.Marker(
            location=[lat, lon],                          # Folium: [lat, lon]
            popup=popup,
            tooltip=f"Veiculo {veiculo['veiculo_id']}",
            icon=folium.Icon(color=cor, icon="truck", prefix="fa"),
        ).add_to(mapa)

    return mapa


def grafico_temperatura(historico: pd.DataFrame) -> "px.line":
    """Historico de temperatura por veiculo.

    Este e o grafico que o seed original do enunciado nao conseguiria
    alimentar: com uma leitura por veiculo, a "linha" seria um ponto.
    """
    figura = px.line(
        historico,
        x="timestamp",
        y="temperatura",
        color="veiculo_id",
        markers=False,
        labels={
            "timestamp": "Horario da leitura",
            "temperatura": "Temperatura (C)",
            "veiculo_id": "Veiculo",
        },
        title="Variacao da temperatura da carga, por veiculo",
    )
    # Linha de referencia do congelamento: separa visualmente os regimes
    figura.add_hline(y=0, line_dash="dot", line_color="#a0aec0",
                     annotation_text="0 C")
    figura.update_layout(hovermode="x unified", height=380)
    return figura


def grafico_status_motoristas(cadastro: pd.DataFrame) -> "px.bar":
    """Distribuicao dos motoristas por status.

    Vem do SQLite - e o unico grafico do painel alimentado pelo lado
    relacional, o que ajuda a mostrar na apresentacao que os dois bancos estao
    de fato em uso.
    """
    contagem = (
        cadastro.groupby("status_motorista")
        .size()
        .reset_index(name="quantidade")
        .sort_values("quantidade", ascending=False)
    )
    figura = px.bar(
        contagem,
        x="status_motorista",
        y="quantidade",
        text="quantidade",
        labels={"status_motorista": "Status", "quantidade": "Motoristas"},
        title="Distribuicao dos motoristas por status",
    )
    figura.update_traces(textposition="outside")
    figura.update_layout(height=380, yaxis_title="Motoristas", xaxis_title="")
    return figura


def simular_movimento(colecao) -> int:
    """Gera uma nova leitura para cada veiculo. (Desafio bonus.)

    Parte da posicao atual de cada um, desloca um pouco e sacode os sensores.
    Como o resto do sistema sempre pergunta "qual a leitura mais recente", o
    ponto novo passa a ser o atual sem que nada mais precise mudar.

    E aqui esta o motivo de posicoes_atuais() ter sido escrita com agregacao
    desde o inicio, e nao como um find() simples: a partir do segundo clique
    neste botao existem duas ou mais leituras por veiculo, e um find() sem
    ordenacao passaria a devolver um ponto qualquer do historico. O mapa
    mostraria o caminhao onde ele ja esteve, a tabela mostraria temperatura
    velha, e nada acusaria o problema.
    """
    novos = []
    for atual in posicoes_atuais(colecao):
        lon, lat = atual["location"]["coordinates"]
        velocidade = max(0, atual["velocidade"] + random.randint(-10, 10))

        # parado nao anda; em movimento, desloca proporcionalmente a velocidade
        deslocamento = 0.0 if velocidade == 0 else velocidade / 20000
        novos.append(
            {
                "veiculo_id": atual["veiculo_id"],
                "location": {
                    "type": "Point",
                    "coordinates": [
                        round(lon + random.uniform(-deslocamento, deslocamento), 6),
                        round(lat + random.uniform(-deslocamento, deslocamento), 6),
                    ],
                },
                "temperatura": round(atual["temperatura"] + random.uniform(-0.4, 0.4), 1),
                "velocidade": int(velocidade),
                "timestamp": datetime.now(timezone.utc).replace(microsecond=0),
            }
        )

    if novos:
        colecao.insert_many(novos)
    return len(novos)


# =====================================================================
# 7. APLICACAO STREAMLIT
# =====================================================================

def barra_lateral() -> dict:
    """Filtros e acoes. Devolve o que o usuario escolheu."""
    st.sidebar.header("Ponto de apoio e busca")

    latitude = st.sidebar.number_input(
        "Latitude de referencia", value=PONTO_APOIO["lat"],
        format="%.4f", step=0.0100,
    )
    longitude = st.sidebar.number_input(
        "Longitude de referencia", value=PONTO_APOIO["lon"],
        format="%.4f", step=0.0100,
    )
    raio = st.sidebar.slider(
        "Raio de busca (km)", min_value=1.0, max_value=50.0,
        value=10.0, step=0.5,
        help="Convertido para metros antes de ir para o $geoNear.",
    )
    mostrar_rota = st.sidebar.checkbox("Mostrar a rota das ultimas 3 horas", value=True)

    st.sidebar.divider()
    st.sidebar.header("Dados")
    simular = st.sidebar.button("Simular movimentacao", use_container_width=True,
                                help="Gera uma leitura nova para cada veiculo.")
    recarregar = st.sidebar.button("Recarregar a base de teste", use_container_width=True,
                                   help="Apaga a telemetria e gera o historico do zero.")

    return {
        "lat": latitude, "lon": longitude, "raio": raio,
        "mostrar_rota": mostrar_rota, "simular": simular, "recarregar": recarregar,
    }


def secao_mapa(colecao, opcoes: dict) -> list[dict]:
    """Modulo 2 - geoprocessamento e busca por raio."""
    st.subheader("Veiculos no raio de busca")

    encontrados = veiculos_no_raio(colecao, opcoes["lon"], opcoes["lat"], opcoes["raio"])
    total_frota = len(posicoes_atuais(colecao))

    st.caption(
        f"{len(encontrados)} de {total_frota} veiculos estao a ate "
        f"{opcoes['raio']:g} km de ({opcoes['lat']:.4f}, {opcoes['lon']:.4f}). "
        f"Consulta feita com $geoNear sobre o indice 2dsphere."
    )

    rotas = rotas_recentes(colecao, horas=3) if opcoes["mostrar_rota"] else None
    mapa = desenhar_mapa(
        {"nome": "Ponto de apoio", "lat": opcoes["lat"], "lon": opcoes["lon"]},
        opcoes["raio"], encontrados, rotas,
    )
    # returned_objects=[] impede que mover ou dar zoom no mapa dispare uma
    # reexecucao do script inteiro. Sem isso, cada arrastar recarrega tudo.
    st_folium(mapa, width=None, height=460, returned_objects=[])

    if encontrados:
        tabela = pd.DataFrame(
            {
                "Veiculo": d["veiculo_id"],
                "Distancia (km)": round(d["distancia_m"] / 1000, 2),
                "Temperatura (C)": d["temperatura"],
                "Velocidade (km/h)": d["velocidade"],
            }
            for d in encontrados
        )
        st.dataframe(tabela, hide_index=True, use_container_width=True)
    else:
        st.info("Nenhum veiculo dentro do raio. Aumente a distancia na barra lateral.")

    return encontrados


def secao_visao_unificada(conexao, colecao) -> pd.DataFrame:
    """Modulo 3 - o cruzamento entre os dois bancos."""
    st.subheader("Visao unificada da frota")
    st.caption(
        "Cadastro vindo do SQLite cruzado com a ultima telemetria do MongoDB. "
        "Nao existe JOIN entre bancos diferentes: cada lado e consultado no seu "
        "proprio banco e o cruzamento acontece em memoria, com pandas."
    )

    unificada = visao_unificada(conexao, colecao)
    colunas = [
        "Motorista", "Placa", "Modelo", "Status",
        "Ultima Temperatura (C)", "Velocidade (km/h)",
        "Coordenadas (lat, lon)", "Leitura em",
    ]
    visiveis = [c for c in colunas if c in unificada.columns]

    # O destaque em vermelho marca a linha inteira do veiculo acima do limite.
    # O formato explicito evita que o pandas mostre "4.200000": a temperatura
    # vem do sensor com uma casa decimal e e assim que ela deve ser lida.
    estilo = (
        unificada[visiveis]
        .style.apply(
            lambda linha: [
                "background-color: #fed7d7"
                if unificada.loc[linha.name, "acima_do_limite"] else ""
                for _ in linha
            ],
            axis=1,
        )
        .format({
            "Ultima Temperatura (C)": "{:.1f}",
            "Velocidade (km/h)": "{:.0f}",
            "Leitura em": lambda t: t.strftime("%d/%m %H:%M") if pd.notna(t) else "-",
        })
    )

    st.dataframe(estilo, hide_index=True, use_container_width=True)
    return unificada


def secao_dashboard(conexao, colecao, unificada: pd.DataFrame) -> None:
    """Modulo 4 - indicadores e graficos."""
    st.subheader("Painel analitico")

    historico = historico_telemetria(colecao)
    cadastro = ler_cadastro(conexao)

    ativos = int((unificada["Status"] == "Ativo").sum())
    media_temperatura = float(unificada["Ultima Temperatura (C)"].mean())
    alertas = int(unificada["acima_do_limite"].sum())

    coluna1, coluna2, coluna3 = st.columns(3)
    coluna1.metric("Veiculos com motorista ativo", f"{ativos} de {len(unificada)}")
    coluna2.metric("Temperatura media da carga", f"{media_temperatura:.1f} C")
    coluna3.metric(f"Alertas de velocidade (> {LIMITE_VELOCIDADE} km/h)", alertas)

    # A media de temperatura esta no enunciado, entao ela aparece. Mas vale
    # registrar que, sozinha, ela nao descreve nada: a frota mistura carga
    # congelada (-18 C), refrigerada (4 C) e seca (22 C). A media dessas tres
    # cai perto de 2 C, que nao e a temperatura de caminhao nenhum. Sao tres
    # regimes distintos somados, e nao uma variacao em torno de um valor.
    st.caption(
        "A temperatura media agrega tres regimes de carga diferentes "
        "(congelada, refrigerada e seca) e por isso nao descreve nenhum "
        "veiculo em particular. A leitura util e a temperatura por veiculo, "
        "no grafico abaixo."
    )

    grafico1, grafico2 = st.columns([3, 2])
    with grafico1:
        st.plotly_chart(grafico_temperatura(historico), use_container_width=True)
    with grafico2:
        st.plotly_chart(grafico_status_motoristas(cadastro), use_container_width=True)


def main() -> None:
    st.set_page_config(page_title="GeoLog - LogiTech Express",
                       page_icon=None, layout="wide")

    st.title("GeoLog - Telemetria da frota LogiTech Express")
    st.markdown(
        "Persistencia poliglota: **SQLite** para o cadastro de motoristas e "
        "veiculos, **MongoDB** para a telemetria geoespacial."
    )

    opcoes = barra_lateral()

    try:
        estado = preparar_bancos(recarregar=opcoes["recarregar"])
    except Exception as erro:
        st.error(
            "Nao foi possivel conectar ao MongoDB em "
            f"`{MONGO_URI}`.\n\nDetalhe: {erro}"
        )
        st.stop()

    conexao, colecao = estado["conexao_sqlite"], estado["colecao"]

    if opcoes["recarregar"]:
        st.sidebar.success(f"{estado['documentos_inseridos']} leituras recriadas.")

    if opcoes["simular"]:
        quantidade = simular_movimento(colecao)
        st.sidebar.success(f"{quantidade} leituras novas inseridas.")
        # st.rerun redesenha a pagina com os dados novos sem reiniciar o
        # processo - e o que o desafio bonus pede.
        st.rerun()

    st.sidebar.divider()
    st.sidebar.caption(
        f"MongoDB: {estado['total_telemetria']} leituras\n\n"
        f"SQLite: {len(MOTORISTAS_SEED)} motoristas, {len(VEICULOS_SEED)} veiculos"
    )

    secao_mapa(colecao, opcoes)
    st.divider()
    unificada = secao_visao_unificada(conexao, colecao)
    st.divider()
    secao_dashboard(conexao, colecao, unificada)


# O Streamlit executa o arquivo como __main__, entao esta guarda funciona para
# ele. Ela tambem permite importar o modulo num teste sem subir a interface.
if __name__ == "__main__":
    main()
