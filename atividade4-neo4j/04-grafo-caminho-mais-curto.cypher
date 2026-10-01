// =====================================================================
// ATIVIDADE 4 - Parte 4: segundo grafo (slide 150) e caminho mais curto
//                        (slide 152)
// =====================================================================
//
// O grafo do slide tem sete pessoas e oito ligacoes Segue, todas com seta
// DUPLA - ou seja, cada ligacao sao dois relacionamentos:
//
//   Rafael <-> Franciele <-> Ana <-> Paulo <-> Carol
//                  |
//              Gabriel <-> Carol
//                  |
//              Renata  <-> Carol
//
// DIVERGENCIA DO MATERIAL: o slide 152 pede "o caminho mais curto entre
// Rafael e Ana", mas as setas vermelhas do slide 150 destacam Rafael e CAROL.
// Rafael->Ana tem 2 saltos e um caminho unico; Rafael->Carol tem 3 saltos e
// caminhos concorrentes, que e o exercicio interessante. Entrego os dois.

MATCH (n) DETACH DELETE n;

CREATE (rafael:Pessoa    { nome: 'Rafael' })
CREATE (ana:Pessoa       { nome: 'Ana' })
CREATE (paulo:Pessoa     { nome: 'Paulo' })
CREATE (carol:Pessoa     { nome: 'Carol' })
CREATE (franciele:Pessoa { nome: 'Franciele' })
CREATE (gabriel:Pessoa   { nome: 'Gabriel' })
CREATE (renata:Pessoa    { nome: 'Renata' })

// cada seta dupla do slide vira dois relacionamentos
CREATE (rafael)-[:SEGUE]->(franciele), (franciele)-[:SEGUE]->(rafael)
CREATE (franciele)-[:SEGUE]->(ana),    (ana)-[:SEGUE]->(franciele)
CREATE (ana)-[:SEGUE]->(paulo),        (paulo)-[:SEGUE]->(ana)
CREATE (paulo)-[:SEGUE]->(carol),      (carol)-[:SEGUE]->(paulo)
CREATE (franciele)-[:SEGUE]->(gabriel),(gabriel)-[:SEGUE]->(franciele)
CREATE (gabriel)-[:SEGUE]->(carol),    (carol)-[:SEGUE]->(gabriel)
CREATE (gabriel)-[:SEGUE]->(renata),   (renata)-[:SEGUE]->(gabriel)
CREATE (renata)-[:SEGUE]->(carol),     (carol)-[:SEGUE]->(renata);

// Conferencia
MATCH (p:Pessoa) RETURN count(p) AS pessoas;
MATCH ()-[r:SEGUE]->() RETURN count(r) AS relacionamentos_segue;


// ---------------------------------------------------------------------
// Caminho mais curto entre Rafael e Ana  (o que o slide 152 pede em texto)
// ---------------------------------------------------------------------
MATCH caminho = shortestPath( (a:Pessoa { nome:'Rafael' })-[:SEGUE*]-(b:Pessoa { nome:'Ana' }) )
RETURN [n IN nodes(caminho) | n.nome] AS caminho, length(caminho) AS saltos;


// ---------------------------------------------------------------------
// Caminho mais curto entre Rafael e Carol  (o que as setas do slide 150
// destacam) - aqui ha caminhos concorrentes, e por isso e o caso interessante
// ---------------------------------------------------------------------
MATCH caminho = shortestPath( (a:Pessoa { nome:'Rafael' })-[:SEGUE*]-(b:Pessoa { nome:'Carol' }) )
RETURN [n IN nodes(caminho) | n.nome] AS caminho, length(caminho) AS saltos;

// Todos os caminhos mais curtos.
//
// ATENCAO ao DISTINCT: sem ele esta consulta devolve o MESMO caminho 8 vezes.
// Nao e defeito - e que o caminho do Neo4j percorre RELACIONAMENTOS, nao nos,
// e cada ligacao do slide (seta dupla) sao dois relacionamentos dirigidos.
// Com 3 ligacoes no caminho, sao 2x2x2 = 8 combinacoes de arestas que
// atravessam exatamente a mesma sequencia de pessoas.
MATCH caminho = allShortestPaths( (a:Pessoa { nome:'Rafael' })-[:SEGUE*]-(b:Pessoa { nome:'Carol' }) )
RETURN DISTINCT [n IN nodes(caminho) | n.nome] AS caminho, length(caminho) AS saltos;

// Os caminhos mais longos sem repetir pessoa, para dar a dimensao do que o
// shortestPath evitou percorrer.
MATCH caminho = (a:Pessoa { nome:'Rafael' })-[:SEGUE*..6]-(b:Pessoa { nome:'Carol' })
WHERE all(n IN nodes(caminho) WHERE single(x IN nodes(caminho) WHERE x = n))
RETURN DISTINCT [n IN nodes(caminho) | n.nome] AS caminho, length(caminho) AS saltos
ORDER BY saltos DESC LIMIT 5;
