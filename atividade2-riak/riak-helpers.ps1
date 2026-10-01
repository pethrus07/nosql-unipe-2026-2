# Funcoes compartilhadas pelas duas etapas da Atividade 2 (Riak via HTTP).
#
# Tres armadilhas que estas funcoes existem para evitar:
#
# 1. No PowerShell, "curl" e apelido de Invoke-WebRequest. Tem de ser curl.exe.
#
# 2. Ler o corpo sem olhar o status. Um GET em chave inexistente devolve HTTP
#    404 com o corpo "not found" - que, usado sem conferir, vira VALOR gravado
#    no banco. Foi o que aconteceu na primeira rodada desta atividade:
#    professores/Leonardo ficou com a string "not found" como idade.
#    Por isso Ler() devolve status e corpo separados, e quem chama decide.
#
# 3. Escopo. A versao anterior guardava a URL base em $script:B. Quando este
#    arquivo e carregado por dot-source de DENTRO de outro script tambem
#    carregado por dot-source - que e como o capturar-terminal.ps1 roda - a
#    variavel nao resolvia dentro das funcoes: o curl recebia URL vazia,
#    devolvia nada, e [int]("") virava 0. O sintoma era "HTTP 0" em tudo.
#    Uma FUNCAO nao tem esse problema: resolucao de comando nao depende de
#    escopo de variavel.

function RiakBase { "http://localhost:8098/buckets" }

function Ler($bucket, $chave) {
    # -w junta o status no fim da saida; a ultima linha e o codigo
    $saida = curl.exe -s -w "`n%{http_code}" "$(RiakBase)/$bucket/keys/$chave"
    $linhas = @($saida -split "`n")
    $status = [int]$linhas[-1]
    [pscustomobject]@{
        Status = $status
        Corpo  = if ($linhas.Count -gt 1) { ($linhas[0..($linhas.Count - 2)] -join "`n") } else { "" }
        Ok     = ($status -ge 200 -and $status -lt 300)
    }
}

function Guardar($bucket, $chave, $valor) {
    [int](curl.exe -s -o NUL -w "%{http_code}" -X PUT "$(RiakBase)/$bucket/keys/$chave" `
          -H "Content-Type: text/plain" -d "$valor")
}

function Apagar($bucket, $chave) {
    [int](curl.exe -s -o NUL -w "%{http_code}" -X DELETE "$(RiakBase)/$bucket/keys/$chave")
}

function Chaves($bucket) {
    $j = curl.exe -s "$(RiakBase)/$bucket/keys?keys=true" | ConvertFrom-Json
    @($j.keys | Sort-Object)
}

function MostrarChaves($bucket) {
    $k = @(Chaves $bucket)
    "  {0,-14} {1}" -f "$bucket :", $(if ($k.Count) { $k -join ', ' } else { '(vazio)' })
}
