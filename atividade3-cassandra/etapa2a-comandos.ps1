# Atividade 3 - Etapa 2 (parte A): alterar o cargo de Theo e excluir Afonso.
# Pressupoe a Etapa 1 recem-executada.

function CQL($sql) {
    Write-Host ""
    Write-Host "cqlsh> $sql" -ForegroundColor Cyan
    docker exec unipe-cassandra cqlsh -k unipe -e $sql
}

Write-Host ""
Write-Host "-- estado antes --" -ForegroundColor DarkGray
docker exec unipe-cassandra cqlsh -k unipe -e "SELECT nome, cargo FROM cadastro;"

# O WHERE do UPDATE e do DELETE exige a chave primaria: em Cassandra nao
# existe "WHERE nome = 'Theo'".
CQL "UPDATE cadastro SET cargo = 'funcionario' WHERE id = 04b57f0e-33df-11e5-a151-feff819cdc9f;"
CQL "DELETE FROM cadastro WHERE id = 1a8d649a-33df-11e5-a151-feff819cdc9f;"

Write-Host ""
Write-Host "-- estado depois: Theo funcionario, Afonso removido --" -ForegroundColor DarkGray
docker exec unipe-cassandra cqlsh -k unipe -e "SELECT nome, cargo FROM cadastro;"
