<#
.SYNOPSIS
    Testa se um servidor DNS (o Pi-hole) esta bloqueando dominios de anuncio.

.DESCRIPTION
    Pergunta ao servidor informado o endereco de alguns dominios de anuncio e de
    alguns sites normais. O Pi-hole responde 0.0.0.0 (ou nada) para o que bloqueia.
    No fim, mostra um resumo e sai com codigo 0 se tudo estiver como esperado.

.PARAMETER Servidor
    IP do Pi-hole, por exemplo 192.168.0.50.

.EXAMPLE
    .\testar-pihole.ps1 -Servidor 192.168.0.50
#>
param(
    [Parameter(Mandatory = $true)]
    [string]$Servidor
)

$dominiosDeAnuncio = @(
    'doubleclick.net',
    'ad.doubleclick.net',
    'googleadservices.com',
    'adservice.google.com'
)

$dominiosNormais = @(
    'www.google.com',
    'www.wikipedia.org',
    'github.com'
)

function Get-RespostaDns {
    param(
        [string]$Dominio,
        [string]$ServidorDns
    )
    try {
        $respostas = Resolve-DnsName -Name $Dominio -Server $ServidorDns -Type A -DnsOnly -QuickTimeout -ErrorAction Stop
    }
    catch {
        # Sem resposta valida (NXDOMAIN ou servidor fora do ar)
        return [pscustomobject]@{ Ips = @(); Erro = $_.Exception.Message }
    }
    $ips = @($respostas | Where-Object { $_.Type -eq 'A' } | ForEach-Object { $_.IPAddress })
    return [pscustomobject]@{ Ips = $ips; Erro = $null }
}

function Test-Bloqueado {
    param([object]$Resposta)
    # Bloqueado = nenhum IP de verdade (so 0.0.0.0 ou nada)
    $ipsReais = @($Resposta.Ips | Where-Object { $_ -ne '0.0.0.0' })
    return ($ipsReais.Count -eq 0)
}

Write-Host ""
Write-Host "Testando o servidor DNS $Servidor" -ForegroundColor Cyan
Write-Host ""

# 1) O servidor responde?
$teste = Get-RespostaDns -Dominio 'www.google.com' -ServidorDns $Servidor
if ($teste.Erro -and $teste.Ips.Count -eq 0) {
    Write-Host "ERRO: o servidor $Servidor nao respondeu." -ForegroundColor Red
    Write-Host "Confira se o Pi-hole esta ligado, se o IP esta certo e se a porta 53 esta liberada no firewall."
    exit 2
}

$falhas = 0

Write-Host "Dominios de anuncio (devem ser BLOQUEADOS):"
foreach ($dominio in $dominiosDeAnuncio) {
    $resposta = Get-RespostaDns -Dominio $dominio -ServidorDns $Servidor
    $ipsTexto = if ($resposta.Ips.Count -gt 0) { ($resposta.Ips | Select-Object -First 2) -join ', ' } else { 'sem IP' }
    if (Test-Bloqueado $resposta) {
        Write-Host ("  [OK]    {0,-25} -> {1}" -f $dominio, $ipsTexto) -ForegroundColor Green
    }
    else {
        Write-Host ("  [FALHA] {0,-25} -> {1}  (nao foi bloqueado)" -f $dominio, $ipsTexto) -ForegroundColor Red
        $falhas++
    }
}

Write-Host ""
Write-Host "Sites normais (devem FUNCIONAR):"
foreach ($dominio in $dominiosNormais) {
    $resposta = Get-RespostaDns -Dominio $dominio -ServidorDns $Servidor
    $ipsTexto = if ($resposta.Ips.Count -gt 0) { ($resposta.Ips | Select-Object -First 2) -join ', ' } else { 'sem IP' }
    if (Test-Bloqueado $resposta) {
        Write-Host ("  [FALHA] {0,-25} -> {1}  (bloqueado por engano)" -f $dominio, $ipsTexto) -ForegroundColor Red
        $falhas++
    }
    else {
        Write-Host ("  [OK]    {0,-25} -> {1}" -f $dominio, $ipsTexto) -ForegroundColor Green
    }
}

$total = $dominiosDeAnuncio.Count + $dominiosNormais.Count
Write-Host ""
if ($falhas -eq 0) {
    Write-Host "Resultado: $total de $total testes OK. O Pi-hole esta funcionando." -ForegroundColor Green
    exit 0
}
else {
    Write-Host "Resultado: $falhas de $total testes falharam." -ForegroundColor Yellow
    exit 1
}
