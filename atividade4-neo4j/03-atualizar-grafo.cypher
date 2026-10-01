// =====================================================================
// ATIVIDADE 4 - Parte 3: atualizar o grafo (slide 149)
// =====================================================================

// 1) Informe que Carol casou
//    Carol nao tinha a propriedade estadoCivil; o SET cria a propriedade.
MATCH (c:Pessoa { nome: 'Carol' })
SET c.estadoCivil = 'Casada'
RETURN c.nome AS nome, c.estadoCivil AS estado_civil;

// 2) Gabriel saiu da rede, portanto exclua ele do grafo
//
//    ATENCAO: "DELETE g" sozinho FALHA, com a mensagem
//       Cannot delete node<0>, because it still has relationships.
//    O Neo4j se recusa a deixar relacionamento apontando para o vazio - e a
//    integridade referencial que o MongoDB nao tem. DETACH DELETE apaga o no
//    e, junto, todos os relacionamentos dele.
MATCH (g:Pessoa { nome: 'Gabriel' })
DETACH DELETE g;

// 3) Cadastre um novo usuario (Linda, EUA, Solteira)
CREATE (l:Pessoa { nome: 'Linda', pais: 'EUA', estadoCivil: 'Solteira' })
RETURN l.nome AS criado, l.pais AS pais, l.estadoCivil AS estado_civil;

// 4) Faca com que Linda siga Carol e vice-versa
//    Sao dois relacionamentos distintos: em grafo a direcao e parte da aresta.
MATCH (l:Pessoa { nome: 'Linda' }), (c:Pessoa { nome: 'Carol' })
CREATE (l)-[:SEGUE]->(c)
CREATE (c)-[:SEGUE]->(l);

// 5) Faca com que Linda adicione uma foto com a legenda "Ingressando na rede!"
MATCH (l:Pessoa { nome: 'Linda' })
CREATE (l)-[:ADICIONOU]->(f:Foto { legenda: 'Ingressando na rede!' })
RETURN f.legenda AS foto_criada;

// 6) Faca com que Carol curta a foto, com a data de hoje
MATCH (c:Pessoa { nome: 'Carol' }), (f:Foto { legenda: 'Ingressando na rede!' })
CREATE (c)-[:CURTIU { data: date() }]->(f);

// 7) A quantidade de curtidas que uma foto recebeu
MATCH (:Pessoa)-[cur:CURTIU]->(f:Foto { legenda: 'Ingressando na rede!' })
RETURN f.legenda AS foto, count(cur) AS curtidas;

// Conferencia do estado final
MATCH (n) RETURN labels(n)[0] AS tipo, properties(n) AS propriedades ORDER BY tipo, propriedades.nome;

MATCH (a)-[r]->(b)
RETURN a.nome AS de, type(r) AS relacionamento,
       coalesce(b.nome, b.legenda) AS para, properties(r) AS props;
