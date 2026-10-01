# Atividade 3 - Etapa 2 (parte B): buscar por cargo.
# Pressupoe a Etapa 1 e a parte A executadas, e o indice AINDA NAO criado -
# o primeiro SELECT precisa falhar para a demonstracao fazer sentido.

function CQL($sql) {
    Write-Host ""
    Write-Host "cqlsh> $sql" -ForegroundColor Cyan
    docker exec unipe-cassandra cqlsh -k unipe -e $sql
}

Write-Host ""
Write-Host "1) buscar os professores SEM indice: o Cassandra RECUSA" -ForegroundColor Yellow
CQL "SELECT nome, cargo FROM cadastro WHERE cargo = 'professor';"

Write-Host ""
Write-Host "2) o proprio erro sugere ALLOW FILTERING - funciona, mas varre tudo" -ForegroundColor Yellow
CQL "SELECT nome, cargo FROM cadastro WHERE cargo = 'professor' ALLOW FILTERING;"

Write-Host ""
Write-Host "3) a saida correta: indice secundario em cargo" -ForegroundColor Yellow
CQL "CREATE INDEX idx_cadastro_cargo ON cadastro (cargo);"
Start-Sleep -Seconds 2
CQL "SELECT nome, cargo FROM cadastro WHERE cargo = 'professor';"
CQL "SELECT nome, cargo FROM cadastro WHERE cargo = 'aluno';"
