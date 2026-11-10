# Resultados da validação

Execução das [ferramentas de validação](ferramentas/) em **10/11/2026**.

| Projeto | Como foi validado | Resultado |
|---|---|---|
| 01 · Rede doméstica | Simulador lógico sobre `configs/ISP.txt` + valores do passo a passo | ✅ |
| 02 · Wireshark | **Captura real** com tshark (`captura_automatica.ps1`) | ✅ |
| 03 · VLANs | Simulador lógico sobre as configs do R1, SW1 e SW2 | ✅ Matriz idêntica à do README |
| 04 · OSPF | Simulador lógico sobre as configs do R-SP, R-RJ e R-BH | ✅ Failover e autenticação conforme o README |
| 05 · Pi-hole | `testar-pihole.ps1` contra um DNS que bloqueia anúncios | ✅ 7 de 7 |

> Os projetos 01, 03 e 04 foram validados por **simulação lógica** das configurações. A montagem no Cisco Packet Tracer, com prints, está em andamento.

---

## 02 · Captura real

**Login em HTTP: a senha aparece em texto puro**
```
Pacotes HTTP:
4   GET   /
8         /        200
16  POST  /login
20        /login   200

Conteudo do POST (o que um atacante le):
usuario,senha   aluno.teste,SenhaFalsa123
```

**Handshake TCP**
```
1  54489 → 8080 [SYN]
2  8080 → 54489 [SYN, ACK]
3  54489 → 8080 [ACK]
```

**DNS e HTTPS**
```
DNS:   Standard query A www.wikipedia.org
       Standard query response A www.wikipedia.org CNAME dyna.wikimedia.org A 195.200.68.224

HTTPS - nome do site visível (SNI):   195.200.68.224   www.wikipedia.org
HTTPS - conteúdo criptografado:       1514 bytes  dea478f49d7a3cb6fdd7c59ff4e981a29a1c9330...
```
**Conclusão:** com HTTP, quem está na mesma rede lê a senha. Com HTTPS, vê apenas o nome do site.

---

## 03 · Rede corporativa com VLANs

```
Aparelho             Switch/porta          VLAN  IP (DHCP)
PC-FIN-1             SW1 FastEthernet0/1   10    192.168.10.11
PC-RH-1              SW1 FastEthernet0/11  20    192.168.20.11
PC-TI-1              SW2 FastEthernet0/1   30    192.168.30.21
Notebook-VISIT-1     SW2 FastEthernet0/11  40    192.168.40.11

Matriz de ping (linha -> coluna):
            Financeiro  RH   TI   Visitantes  Internet
Financeiro      ✅      ❌   ✅      ❌          ✅
RH              ❌      ✅   ✅      ❌          ✅
TI              ✅      ✅   ✅      ❌          ✅
Visitantes      ❌      ❌   ❌      ✅          ✅

PC-FIN-1          abre http://intranet.empresa.lab: ✅
Notebook-VISIT-1  abre http://intranet.empresa.lab: ❌
PC-TI-1           ssh -l admin 192.168.30.1 (R1):   ✅ entra
PC-RH-1           ssh -l admin 192.168.20.1 (R1):   ❌ recusado
Telnet no R1: ❌ recusado (transport input ssh)
```

---

## 04 · WAN com OSPF

**Situação normal**
```
R-RJ# show ip route ospf
  O  192.168.1.0/24   [110/2] via 10.0.0.1, GigabitEthernet0/1
  O  192.168.3.0/24   [110/3] via 10.0.0.1, GigabitEthernet0/1

tracert PC-RJ -> PC-BH:  192.168.2.1 → 10.0.0.1 → 10.0.0.6 → 192.168.3.11
```

**Link SP–BH derrubado (`shutdown` no R-SP G0/2)**
```
R-BH# show ip route ospf
  O  192.168.1.0/24   [110/102] via 10.0.0.9, GigabitEthernet0/2
  O  192.168.2.0/24   [110/101] via 10.0.0.9, GigabitEthernet0/2

tracert PC-BH -> Servidor-SP:  192.168.3.1 → 10.0.0.9 → 10.0.0.1 → 192.168.1.10
```
O tráfego passou sozinho para o **link de backup** pelo Rio de Janeiro. Com `no shutdown`, voltou ao caminho principal (custo 2).

**Chave OSPF errada no R-BH:** o vizinho R-SP é descartado. A autenticação impede roteadores não autorizados.

---

## 05 · Bloqueio por DNS

```
Dominios de anuncio (devem ser BLOQUEADOS):
  [OK]    doubleclick.net           -> 0.0.0.0
  [OK]    ad.doubleclick.net        -> 0.0.0.0
  [OK]    googleadservices.com      -> 0.0.0.0
  [OK]    adservice.google.com      -> 0.0.0.0

Sites normais (devem FUNCIONAR):
  [OK]    www.google.com            -> 142.251.155.119, ...
  [OK]    www.wikipedia.org         -> 195.200.68.224
  [OK]    github.com                -> 4.228.31.150

Resultado: 7 de 7 testes OK.
```
Teste feito com o [bloqueador_dns_demo.py](05-pihole-dns/bloqueador_dns_demo.py), que aplica o mesmo princípio do Pi-hole. A execução com o Pi-hole em Docker está em andamento.
