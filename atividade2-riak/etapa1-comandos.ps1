# Atividade 2 - Etapa 1: inserir 6 objetos chave-valor em 3 buckets via HTTP
# e listar as chaves de cada bucket.

. (Join-Path $PSScriptRoot 'riak-helpers.ps1')
$BUCKETS = 'professores','alunos','funcionarios'

# Limpeza do estado de execucoes anteriores.
# Apagar e regravar a MESMA chave no ato faz o PUT se perder: o Riak guarda um
# tombstone por ~3 s (delete_mode padrao) e ele vence a escrita seguinte.
$apagou = $false
foreach ($b in $BUCKETS) {
    foreach ($k in (Chaves $b)) { Apagar $b $k | Out-Null; $apagou = $true }
}
if ($apagou) { Start-Sleep -Seconds 8 }

Write-Host ""
Write-Host "1) inserir os 6 objetos chave-valor (PUT HTTP)" -ForegroundColor Yellow
@(
 @('professores','Thyago',35), @('professores','Afonso',28),
 @('alunos','Fernanda',32),    @('alunos','Theo',12),
 @('funcionarios','Sophia',20),@('funcionarios','Leonardo',15)
) | ForEach-Object {
    $b, $k, $v = $_
    $st = Guardar $b $k $v
    "  PUT {0,-26} idade={1,-3}  HTTP {2}" -f "$b/$k", $v, $st
}

Write-Host ""
Write-Host "2) ler cada objeto de volta (GET HTTP)" -ForegroundColor Yellow
@(
 @('professores','Thyago'), @('professores','Afonso'),
 @('alunos','Fernanda'),    @('alunos','Theo'),
 @('funcionarios','Sophia'),@('funcionarios','Leonardo')
) | ForEach-Object {
    $b, $k = $_
    $r = Ler $b $k
    "  GET {0,-26} HTTP {1}  idade={2}" -f "$b/$k", $r.Status, $r.Corpo
}

Write-Host ""
Write-Host "3) listar as chaves de cada bucket separadamente" -ForegroundColor Yellow
Start-Sleep -Seconds 3
foreach ($b in $BUCKETS) { MostrarChaves $b }
