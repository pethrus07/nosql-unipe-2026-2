# Atividade 3 - Etapa 1: keyspace unipe, tabela cadastro e os 6 registros do
# slide 99. Roda dentro do console que sera capturado pelo print.
# DROP antes do CREATE para o print mostrar o estado da Etapa 1 mesmo que a
# Etapa 2 ja tenha rodado alguma vez.

function CQL($sql) {
    Write-Host ""
    Write-Host "cqlsh> $sql" -ForegroundColor Cyan
    docker exec unipe-cassandra cqlsh -k unipe -e $sql
}

Write-Host ""
Write-Host "cqlsh> SELECT release_version FROM system.local;" -ForegroundColor Cyan
docker exec unipe-cassandra cqlsh -e "SELECT release_version FROM system.local;"

Write-Host ""
Write-Host "cqlsh> CREATE KEYSPACE unipe WITH replication =" -ForegroundColor Cyan
Write-Host "          {'class':'SimpleStrategy','replication_factor':1};" -ForegroundColor Cyan
docker exec unipe-cassandra cqlsh -e "CREATE KEYSPACE IF NOT EXISTS unipe WITH replication = {'class':'SimpleStrategy','replication_factor':1};"
docker exec unipe-cassandra cqlsh -k unipe -e "DROP TABLE IF EXISTS cadastro;"

CQL "CREATE TABLE cadastro (id uuid PRIMARY KEY, nome text, cargo text);"

Write-Host ""
Write-Host "cqlsh> INSERT INTO cadastro (id, nome, cargo) VALUES (...);   x6" -ForegroundColor Cyan
@(
 "1a8d6a80-33df-11e5-a151-feff819cdc9f|Thyago|professor"
 "1a8d649a-33df-11e5-a151-feff819cdc9f|Afonso|professor"
 "a70ca7ff-6d57-4f89-be89-08421c432bb7|Fernanda|aluno"
 "04b57f0e-33df-11e5-a151-feff819cdc9f|Theo|aluno"
 "c4f408dd-00f3-488e-8800-050d2775bbc7|Sophia|funcionario"
 "04b57c98-33df-11e5-a151-feff819cdc9f|Leonardo|funcionario"
) | ForEach-Object {
    $id, $nome, $cargo = $_ -split '\|'
    Write-Host ("         ({0}, '{1}', '{2}')" -f $id, $nome, $cargo)
    docker exec unipe-cassandra cqlsh -k unipe -e "INSERT INTO cadastro (id, nome, cargo) VALUES ($id, '$nome', '$cargo');"
}

CQL "SELECT nome, cargo, id FROM cadastro;"
