-- =====================================================================
-- ATIVIDADE 3 - Cassandra (slides 98-100)
-- UNIPE - Implementacao e Gerenciamento de Bancos de Dados NoSQL
-- Aluno: Pedro Oliveira
--
-- Executar:
--   docker exec -i unipe-cassandra cqlsh < atividade3.cql
-- =====================================================================


-- =====================================================================
-- ETAPA 1 - Criar o keyspace, a tabela e inserir os 6 registros
-- =====================================================================

-- SimpleStrategy com fator 1: e um no so, em container. Num cluster real
-- seria NetworkTopologyStrategy com fator 3.
CREATE KEYSPACE IF NOT EXISTS unipe
  WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 1};

USE unipe;

DROP TABLE IF EXISTS cadastro;

CREATE TABLE cadastro (
  id    uuid PRIMARY KEY,
  nome  text,
  cargo text
);

INSERT INTO cadastro (id, nome, cargo) VALUES (1a8d6a80-33df-11e5-a151-feff819cdc9f, 'Thyago',    'professor');
INSERT INTO cadastro (id, nome, cargo) VALUES (1a8d649a-33df-11e5-a151-feff819cdc9f, 'Afonso',    'professor');
INSERT INTO cadastro (id, nome, cargo) VALUES (a70ca7ff-6d57-4f89-be89-08421c432bb7, 'Fernanda',  'aluno');
INSERT INTO cadastro (id, nome, cargo) VALUES (04b57f0e-33df-11e5-a151-feff819cdc9f, 'Theo',      'aluno');
INSERT INTO cadastro (id, nome, cargo) VALUES (c4f408dd-00f3-488e-8800-050d2775bbc7, 'Sophia',    'funcionario');
INSERT INTO cadastro (id, nome, cargo) VALUES (04b57c98-33df-11e5-a151-feff819cdc9f, 'Leonardo',  'funcionario');

SELECT id, nome, cargo FROM cadastro;


-- =====================================================================
-- ETAPA 2 - Alterar, excluir e consultar
-- =====================================================================

-- 2.1  Alterar o cargo de Theo para funcionario
--      O WHERE do UPDATE precisa da chave primaria; nao da para escrever
--      "WHERE nome = 'Theo'" em Cassandra.
UPDATE cadastro SET cargo = 'funcionario'
  WHERE id = 04b57f0e-33df-11e5-a151-feff819cdc9f;

-- 2.2  Excluir Afonso
DELETE FROM cadastro
  WHERE id = 1a8d649a-33df-11e5-a151-feff819cdc9f;

SELECT id, nome, cargo FROM cadastro;

-- 2.3  Buscar todos os professores
--      Sem indice isto FALHA. A consulta abaixo esta comentada de proposito
--      para o script nao abortar; o erro esta demonstrado em
--      etapa2-consulta-sem-indice.txt.
--
--      SELECT * FROM cadastro WHERE cargo = 'professor';
--      -> InvalidRequest: Cannot execute this query as it might involve data
--         filtering and thus may have unpredictable performance.
--
--      Duas saidas. A primeira e a que o Cassandra sugere:
SELECT id, nome, cargo FROM cadastro WHERE cargo = 'professor' ALLOW FILTERING;

-- 2.4  Buscar todos os alunos
SELECT id, nome, cargo FROM cadastro WHERE cargo = 'aluno' ALLOW FILTERING;


-- =====================================================================
-- A segunda saida: indice secundario
-- =====================================================================
-- Com o indice, o WHERE por cargo passa a funcionar sem ALLOW FILTERING.

CREATE INDEX IF NOT EXISTS idx_cadastro_cargo ON cadastro (cargo);

SELECT id, nome, cargo FROM cadastro WHERE cargo = 'professor';
SELECT id, nome, cargo FROM cadastro WHERE cargo = 'aluno';
SELECT id, nome, cargo FROM cadastro WHERE cargo = 'funcionario';
