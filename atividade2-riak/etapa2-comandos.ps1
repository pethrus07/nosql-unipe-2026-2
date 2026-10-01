# Atividade 2 - Etapa 2: alterar a idade de Theo, mover Leonardo de bucket,
# excluir Afonso, ler a nova idade de Theo e listar as chaves.
# Pressupoe a Etapa 1 recem-executada.

. (Join-Path $PSScriptRoot 'riak-helpers.ps1')
$BUCKETS = 'professores','alunos','funcionarios'

Write-Host ""
Write-Host "1) alterar a idade de Theo para 25" -ForegroundColor Yellow
"  PUT alunos/Theo = 25   HTTP {0}" -f (Guardar alunos Theo 25)

Write-Host ""
Write-Host "2) Leonardo deixa de ser funcionario e passa a professor" -ForegroundColor Yellow
Write-Host "   nao existe 'mover' em chave-valor: le, grava no destino, apaga na origem" -ForegroundColor DarkGray
$r = Ler funcionarios Leonardo
"  GET    funcionarios/Leonardo   HTTP {0}  idade={1}" -f $r.Status, $r.Corpo
if (-not $r.Ok) {
    # sem esta guarda, o corpo "not found" de um 404 seria gravado como idade
    Write-Host "  ABORTADO: Leonardo nao esta em funcionarios. Rode a Etapa 1 antes." -ForegroundColor Red
    return
}
"  PUT    professores/Leonardo = {0}    HTTP {1}" -f $r.Corpo, (Guardar professores Leonardo $r.Corpo)
"  DELETE funcionarios/Leonardo          HTTP {0}" -f (Apagar funcionarios Leonardo)

Write-Host ""
Write-Host "3) excluir Afonso" -ForegroundColor Yellow
"  DELETE professores/Afonso             HTTP {0}" -f (Apagar professores Afonso)
$r = Ler professores Afonso
"  GET    professores/Afonso             HTTP {0}  ({1})" -f $r.Status, $r.Corpo

Write-Host ""
Write-Host "4) obter a nova idade de Theo e apresentar no console" -ForegroundColor Yellow
$r = Ler alunos Theo
"  GET alunos/Theo   HTTP {0}  idade={1}" -f $r.Status, $r.Corpo

Write-Host ""
Write-Host "5) listar as chaves de cada bucket separadamente" -ForegroundColor Yellow
Write-Host "   a listagem e eventualmente consistente: uma chave recem-apagada" -ForegroundColor DarkGray
Write-Host "   ainda aparece aqui por alguns segundos, mesmo o GET dela ja dando 404" -ForegroundColor DarkGray
Start-Sleep -Seconds 35
foreach ($b in $BUCKETS) { MostrarChaves $b }
