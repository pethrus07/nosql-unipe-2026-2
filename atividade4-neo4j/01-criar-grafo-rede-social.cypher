// =====================================================================
// ATIVIDADE 4 - Neo4j (slides 145-152)
// Parte 1: modelar o grafo da rede social hipotetica do slide 146
// UNIPE - Aluno: Pedro Oliveira
// =====================================================================
//
// O grafo do slide tem tres nos e quatro relacionamentos:
//
//     Gabriel  --Segue-->  Carol
//     Gabriel  <--Segue--  Carol
//     Gabriel  --Curtiu{Data:2019-01-01}-->  Foto
//     Carol    --Adicionou-->                Foto
//
// Repare que Carol NAO tem estado civil no slide. Nao e esquecimento do
// professor: e o que torna possivel a consulta "nome dos usuarios que nao
// possuam Estado Civil cadastrado" da etapa seguinte. Num banco relacional a
// coluna existiria com NULL; aqui a PROPRIEDADE simplesmente nao existe no no.

MATCH (n) DETACH DELETE n;

CREATE (gabriel:Pessoa { nome: 'Gabriel', pais: 'Canada', estadoCivil: 'Namorando' })
CREATE (carol:Pessoa   { nome: 'Carol',   pais: 'Brasil' })
CREATE (foto:Foto      { legenda: 'Meu cachorro' })

CREATE (gabriel)-[:SEGUE]->(carol)
CREATE (carol)-[:SEGUE]->(gabriel)
CREATE (gabriel)-[:CURTIU { data: date('2019-01-01') }]->(foto)
CREATE (carol)-[:ADICIONOU]->(foto);

// Conferencia: o que foi criado
MATCH (n) RETURN labels(n)[0] AS tipo, properties(n) AS propriedades ORDER BY tipo;

MATCH (a)-[r]->(b)
RETURN a.nome AS de, type(r) AS relacionamento,
       coalesce(b.nome, b.legenda) AS para, properties(r) AS props;
