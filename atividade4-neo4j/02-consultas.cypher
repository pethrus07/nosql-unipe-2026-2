// =====================================================================
// ATIVIDADE 4 - Parte 2: extrair informacoes dos usuarios (slide 148)
// =====================================================================

// 1) O nome e o pais de um usuario
MATCH (p:Pessoa { nome: 'Gabriel' })
RETURN p.nome AS nome, p.pais AS pais;

// 2) A legenda de todas as fotos de um usuario
//    "de um usuario" = as que ele ADICIONOU
MATCH (p:Pessoa { nome: 'Carol' })-[:ADICIONOU]->(f:Foto)
RETURN p.nome AS usuario, f.legenda AS legenda;

// 3) A quantidade de pessoas que SEGUE um usuario
//    A direcao da seta e a resposta: quem segue Carol e quem aponta PARA ela.
//    Invertendo a seta a pergunta vira "quantas pessoas Carol segue", que e
//    outra coisa - e neste grafo as duas dao 1 por coincidencia.
MATCH (seguidor:Pessoa)-[:SEGUE]->(:Pessoa { nome: 'Carol' })
RETURN count(seguidor) AS seguidores_de_carol;

// 4) A quantidade de fotos publicadas
MATCH (f:Foto)
RETURN count(f) AS fotos_publicadas;

// 5) Nome dos usuarios que NAO possuam Estado Civil cadastrado
//    Em Neo4j a propriedade ausente nao existe - nao ha "coluna com NULL".
//    IS NULL casa tanto com ausente quanto com nulo.
MATCH (p:Pessoa)
WHERE p.estadoCivil IS NULL
RETURN p.nome AS sem_estado_civil;

// 6) A quantidade de curtidas que uma foto recebeu
MATCH (:Pessoa)-[c:CURTIU]->(f:Foto { legenda: 'Meu cachorro' })
RETURN f.legenda AS foto, count(c) AS curtidas;
