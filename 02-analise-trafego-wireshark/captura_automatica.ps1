<#
.SYNOPSIS
    Roda os experimentos 1, 2, 3 e 6 automaticamente com o tshark (Wireshark em linha de comando).

.DESCRIPTION
    1. Sobe o servidor_login_inseguro.py, captura no loopback e mostra a senha de teste legivel (HTTP).
    2. Captura na placa de rede um acesso HTTPS e uma consulta DNS e mostra o que fica visivel.
    Capture apenas a sua propria rede.

.PARAMETER Interface
    Nome da placa de rede para o experimento HTTPS/DNS (veja com: tshark -D). Padrao: Ethernet.

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File .\captura_automatica.ps1 -Interface Wi-Fi
#>
param([string]$Interface = 'Ethernet')

$tshark = 'C:\Program Files\Wireshark\tshark.exe'
if (-not (Test-Path $tshark)) { Write-Host 'Wireshark nao encontrado. Instale pelo wireshark.org.' -ForegroundColor Red; exit 2 }
$pasta = Split-Path $MyInvocation.MyCommand.Path
$tmp = [System.IO.Path]::GetTempPath()
$pcap1 = Join-Path $tmp 'portfolio_exp1.pcapng'
$pcap2 = Join-Path $tmp 'portfolio_exp2.pcapng'
Remove-Item $pcap1, $pcap2 -ErrorAction SilentlyContinue

# ---------- Experimento 1 e 6: HTTP no loopback ----------
Write-Host "`n[1/2] Capturando login HTTP no loopback..." -ForegroundColor Cyan
$srv = Start-Process py -ArgumentList 'servidor_login_inseguro.py' -WorkingDirectory $pasta -PassThru -WindowStyle Hidden
$cap = Start-Process $tshark -ArgumentList '-i', '\Device\NPF_Loopback', '-f', '"tcp port 8080"', '-w', "`"$pcap1`"", '-a', 'duration:12' -PassThru -WindowStyle Hidden
Start-Sleep 4
curl.exe -s -o NUL http://127.0.0.1:8080/
curl.exe -s -o NUL -d 'usuario=aluno.teste&senha=SenhaFalsa123' http://127.0.0.1:8080/login
$cap.WaitForExit()
Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like '*servidor_login_inseguro*' } |
    ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }

Write-Host "`nPacotes HTTP:"
& $tshark -r $pcap1 -Y 'http' -T fields -e frame.number -e http.request.method -e http.request.uri -e http.response.code
Write-Host "`nConteudo do POST (o que um atacante le):" -ForegroundColor Yellow
& $tshark -r $pcap1 -Y 'http.request.method == "POST"' -T fields -e urlencoded-form.key -e urlencoded-form.value
Write-Host "`nHandshake TCP:"
& $tshark -r $pcap1 -Y 'tcp.stream eq 0 and tcp.len == 0' -c 3 -T fields -e frame.number -e _ws.col.Info

# ---------- Experimentos 2 e 3: HTTPS e DNS ----------
Write-Host "`n[2/2] Capturando DNS e HTTPS na interface '$Interface'..." -ForegroundColor Cyan
$cap = Start-Process $tshark -ArgumentList '-i', "`"$Interface`"", '-f', '"port 53 or port 443"', '-w', "`"$pcap2`"", '-a', 'duration:12' -PassThru -WindowStyle Hidden
Start-Sleep 4
ipconfig /flushdns | Out-Null
nslookup www.wikipedia.org 2>&1 | Out-Null
curl.exe -s -o NUL https://www.wikipedia.org/
$cap.WaitForExit()

Write-Host "`nDNS:"
& $tshark -r $pcap2 -Y 'dns.qry.name == "www.wikipedia.org"' -T fields -e ip.src -e ip.dst -e _ws.col.Info | Select-Object -First 4
Write-Host "`nHTTPS - nome do site visivel no Client Hello (SNI):" -ForegroundColor Yellow
& $tshark -r $pcap2 -Y 'tls.handshake.extensions_server_name contains "wikipedia"' -T fields -e ip.dst -e tls.handshake.extensions_server_name | Select-Object -First 1
Write-Host "`nHTTPS - conteudo criptografado (Application Data):"
& $tshark -r $pcap2 -Y 'tls.app_data' -T fields -e frame.len -e tls.app_data | Select-Object -First 3 | ForEach-Object {
    $p = $_ -split "`t"; '{0} bytes  {1}...' -f $p[0], $p[1].Substring(0, [Math]::Min(48, $p[1].Length))
}
Write-Host "`nCapturas salvas em: $pcap1 e $pcap2 (abra no Wireshark para ver tudo)."
