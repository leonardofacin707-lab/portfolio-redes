# Passo a passo · Rede corporativa com VLANs

Tempo estimado: **2 a 3 horas**. Ferramenta: **Cisco Packet Tracer**.

## Antes de começar: o que é VLAN, em 30 segundos

Imagine um prédio com um único corredor (o switch). A **VLAN** coloca **paredes invisíveis** nesse corredor: o Financeiro fica numa sala, o RH em outra. Mesmo ligados no mesmo switch, eles **não se enxergam**. Para passar de uma sala para outra, é preciso passar pela **portaria** (o roteador), e lá o **porteiro** (a ACL) decide quem pode.

---

## Parte 1 · Equipamentos

| Nome | Modelo |
|---|---|
| R1-EMPRESA | Router **2911** |
| SW1, SW2 | Switch **2960** |
| PC-FIN-1, PC-FIN-2, PC-RH-1, PC-RH-2, PC-TI-1 | **PC** |
| Notebook-VISIT-1, Notebook-VISIT-2 | **Laptop** |
| Servidor-TI | **Server** |

## Parte 2 · Cabos

| De | Porta | Para | Porta | Cabo |
|---|---|---|---|---|
| R1-EMPRESA | G0/0 | SW1 | G0/1 | Copper Straight-Through |
| SW1 | G0/2 | SW2 | G0/2 | **Copper Cross-Over** (switch com switch) |
| PC-FIN-1 | Fa0 | SW1 | Fa0/1 | Straight-Through |
| PC-FIN-2 | Fa0 | SW1 | Fa0/2 | Straight-Through |
| PC-RH-1 | Fa0 | SW1 | Fa0/11 | Straight-Through |
| PC-RH-2 | Fa0 | SW1 | Fa0/12 | Straight-Through |
| PC-TI-1 | Fa0 | SW2 | Fa0/1 | Straight-Through |
| Servidor-TI | Fa0 | SW2 | Fa0/2 | Straight-Through |
| Notebook-VISIT-1 | Fa0 | SW2 | Fa0/11 | Straight-Through |
| Notebook-VISIT-2 | Fa0 | SW2 | Fa0/12 | Straight-Through |

## Parte 3 · Configurar os switches

Para **SW1** e **SW2**: clique no switch → aba **CLI** → Enter → cole o conteúdo de [configs/SW1.txt](configs/SW1.txt) e [configs/SW2.txt](configs/SW2.txt).

> **Dica:** se colar tudo de uma vez der erro em alguma linha, cole em blocos menores (de um `!` até o próximo). O Packet Tracer às vezes "engole" linhas quando a colagem é muito grande.

> **Atenção:** a configuração ativa senha no console. Da próxima vez que abrir o CLI, entre com usuário `admin` e senha `Cisco@Lab26`.

Confira em cada switch:
```
show vlan brief
show interfaces trunk
```
- `show vlan brief`: cada faixa de portas na VLAN certa.
- `show interfaces trunk`: G0/1 e G0/2 (SW1) e G0/2 (SW2) como **trunking**, com as VLANs 10,20,30,40,99.

📸 **Print:** `show vlan brief` do SW1.

## Parte 4 · Configurar o roteador

R1-EMPRESA → CLI → cole [configs/R1-EMPRESA.txt](configs/R1-EMPRESA.txt).

Confira:
```
show ip interface brief
show ip dhcp pool
```
As subinterfaces `G0/0.10`, `.20`, `.30`, `.40`, `.99` devem estar **up / up**.

## Parte 5 · Servidor-TI

1. **Desktop → IP Configuration → Static**: IP `192.168.30.10`, máscara `255.255.255.0`, gateway `192.168.30.1`, DNS `192.168.30.10`.
2. **Services → HTTP**: ligado. Edite o `index.html` com algo como `<h1>Intranet da Empresa</h1>`.
3. **Services → DNS**: ligue e adicione `intranet.empresa.lab` → A Record → `192.168.30.10`.

## Parte 6 · PCs e notebooks

Em todos: **Desktop → IP Configuration → DHCP**. Cada um deve receber um IP da **sua** VLAN:
- PC-FIN → 192.168.10.x
- PC-RH → 192.168.20.x
- PC-TI-1 → 192.168.30.x (a partir de .21)
- Notebooks → 192.168.40.x

Se aparecer `169.254.x.x`, o DHCP não chegou: confira o trunk e as subinterfaces.

## Parte 7 · Testes 📸

Use **Desktop → Command Prompt** em cada aparelho. Anote o IP de cada um e preencha a matriz do README.

Exemplos (troque pelos IPs que seus PCs receberam):

**Do PC-RH-1:**
```
ping 192.168.10.11      (Financeiro: deve FALHAR)
ping 192.168.30.10      (Servidor-TI: deve funcionar)
ping 8.8.8.8            (Internet: deve funcionar)
```

**Do Notebook-VISIT-1:**
```
ping 192.168.40.1       (gateway: funciona)
ping 192.168.30.10      (Servidor-TI: deve FALHAR)
ping 192.168.10.11      (Financeiro: deve FALHAR)
ping 8.8.8.8            (Internet: funciona)
```
E no **Web Browser**: `http://intranet.empresa.lab` → **não** abre.

**Do PC-FIN-1:** Web Browser → `http://intranet.empresa.lab` → **abre**.

**SSH:**
- PC-TI-1 → Command Prompt → `ssh -l admin 192.168.30.1` → senha `Cisco@Lab26` → entra ✅
- PC-TI-1 → `ssh -l admin 192.168.99.11` → entra no SW1 ✅
- PC-RH-1 → `ssh -l admin 192.168.20.1` → recusado ❌

**No R1, veja o porteiro trabalhando:**
```
show access-lists
```
As linhas `deny` mostram quantos pacotes foram barrados ("matches").

> O primeiro ping entre VLANs às vezes perde 1 ou 2 pacotes (ARP). Repita o comando.

**Prints sugeridos:** `show vlan brief`, `show interfaces trunk`, `ipconfig` de um PC de cada VLAN, ping bloqueado do visitante, intranet abrindo no Financeiro e não abrindo no visitante, SSH da TI funcionando e do RH recusado, `show access-lists` com os contadores.

Salve como `rede-corporativa-vlans.pkt` nesta pasta.

---

## Se algo der errado

| Sintoma | Causa provável | Verifique |
|---|---|---|
| PC recebe 169.254.x.x | DHCP não chega | `show interfaces trunk` nos dois switches; VLAN criada nos **dois** switches |
| Subinterface down | Interface física desligada | `no shutdown` em `G0/0` do R1 |
| Ping entre VLANs liberadas falha | Gateway errado no PC | `ipconfig` no PC |
| SSH recusado até pela TI | Chave RSA não foi criada | `show ip ssh` no R1; refaça `crypto key generate rsa general-keys modulus 1024` |
| Tudo bloqueado no RH | Faltou o `permit ip any any` | `show access-lists RH-IN` |
