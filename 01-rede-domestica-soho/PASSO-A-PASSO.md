# Passo a passo · Rede doméstica (SOHO)

Tempo estimado: **1 a 2 horas**. Ferramenta: **Cisco Packet Tracer** (versão 8.x).

> Dica geral do Packet Tracer: os equipamentos ficam na barra inferior. Clique na categoria (ex.: *Network Devices → Routers*), arraste o equipamento para a área de trabalho e clique nele para abrir as abas **Physical**, **Config**, **CLI**/**Desktop** e **GUI**.

---

## Parte 1 · Colocar os equipamentos

| Nome (renomeie na aba Config) | Onde achar | Modelo |
|---|---|---|
| ISP | Network Devices → Routers | **2911** |
| Servidor-Internet | End Devices | **Server** |
| Roteador-Casa | Network Devices → Wireless Devices | **WRT300N** |
| PC-Sala | End Devices | **PC** |
| Impressora | End Devices | **Printer** |
| Notebook | End Devices | **Laptop** |
| Smartphone | End Devices | **Smartphone** |
| Tablet | End Devices | **Tablet** |

## Parte 2 · Ligar os cabos

Use o cabo **Copper Straight-Through** (linha preta contínua) em todos:

| De | Porta | Para | Porta |
|---|---|---|---|
| Servidor-Internet | FastEthernet0 | ISP | GigabitEthernet0/1 |
| ISP | GigabitEthernet0/0 | Roteador-Casa | **Internet** |
| PC-Sala | FastEthernet0 | Roteador-Casa | Ethernet 1 |
| Impressora | FastEthernet0 | Roteador-Casa | Ethernet 2 |

> Repare: a porta **Internet** do roteador de casa é a porta **WAN** que estudamos. As portas Ethernet 1 a 4 são a **LAN**.

## Parte 3 · Roteador da operadora (ISP)

1. Clique no **ISP** → aba **CLI** → tecle Enter.
2. Copie todo o conteúdo de [configs/ISP.txt](configs/ISP.txt) e cole na tela (botão direito → Paste, ou Ctrl+V).
3. Confira com:
   ```
   show ip interface brief
   ```
   As portas G0/0 e G0/1 devem aparecer como **up / up** (G0/0 só fica "up" depois que o Roteador-Casa estiver ligado nela).

## Parte 4 · Servidor da "Internet"

1. **Desktop → IP Configuration** → *Static*:
   - IP: `203.0.113.10` · Máscara: `255.255.255.0`
   - Gateway: `203.0.113.1` · DNS: `203.0.113.10`
2. **Services → HTTP**: deixe ligado. Clique em *edit* no `index.html` e troque o texto por algo seu, por exemplo:
   ```html
   <h1>Funcionou! Rede domestica conectada a Internet.</h1>
   ```
3. **Services → DNS**: ligue (*On*) e adicione:
   - Name: `www.meusite.com` · Type: *A Record* · Address: `203.0.113.10` → **Add**

## Parte 5 · Roteador de casa (WRT300N)

Clique no **Roteador-Casa** → aba **GUI**.

**Setup → Basic Setup**
1. *Internet Setup*: **Automatic Configuration - DHCP** (a operadora entrega o IP).
2. *Router IP*: `192.168.0.1` / `255.255.255.0` (já vem assim).
3. *DHCP Server*: **Enabled** · Start IP: `192.168.0.100` · Maximum users: `50`.
4. *Static DNS 1*: `203.0.113.10`.
5. Role até o fim → **Save Settings**.

**Wireless → Basic Wireless Settings**
1. Network Name (SSID): `CASA-PORTFOLIO`
2. **Save Settings**

**Wireless → Wireless Security**
1. Security Mode: **WPA2 Personal** · Encryption: **AES**
2. Passphrase: `MinhaRede@2026`
3. **Save Settings**

**Administration → Management**
1. Router Password: troque `admin` por uma senha nova (ex.: `AdminCasa@2026`) e confirme.
2. **Save Settings**

> Volte na aba **Status** e confira se o roteador recebeu o IP `200.10.10.2` no lado Internet.

## Parte 6 · Aparelhos com cabo

**PC-Sala** → Desktop → IP Configuration → marque **DHCP**. Deve aparecer um IP 192.168.0.1xx.

**Impressora** → Config → FastEthernet0 → **Static**:
- IP `192.168.0.20` · Máscara `255.255.255.0`

E em Config → Settings: Gateway `192.168.0.1`, DNS `203.0.113.10`.

## Parte 7 · Aparelhos sem fio

**Notebook** (ele vem com placa de rede de cabo; vamos trocar por uma Wi-Fi):
1. Aba **Physical** → clique no botão de **ligar/desligar** do notebook para desligá-lo.
2. Arraste a placa **PT-LAPTOP-NM-1CFE** para fora, de volta para a lista de módulos.
3. Arraste a placa **WPC300N** para o espaço vazio.
4. Ligue o notebook de novo.

**Notebook, Smartphone e Tablet** → **Config → Wireless0**:
- SSID: `CASA-PORTFOLIO`
- Authentication: **WPA2-PSK** · PSK Pass Phrase: `MinhaRede@2026`
- Encryption Type: **AES**
- IP Configuration: **DHCP**

Em alguns segundos aparecem as "ondinhas" ligando cada aparelho ao roteador.

## Parte 8 · Testes (e prints para o portfólio 📸)

No **PC-Sala** → Desktop → **Command Prompt**:

```
ipconfig
ping 192.168.0.1
ping 192.168.0.20
ping 203.0.113.10
tracert 203.0.113.10
```

- O `tracert` mostra o caminho: **roteador de casa → roteador da operadora → servidor**.
- O primeiro ping às vezes perde 1 pacote. É normal: o computador ainda está descobrindo o endereço físico (ARP) do vizinho.

No **Notebook** → Desktop → **Web Browser** → digite `http://www.meusite.com` → a sua página deve abrir.

**Teste de segurança:** coloque um segundo Smartphone, configure o SSID certo mas a **senha errada**. Ele **não** deve conectar.

**Ver o NAT acontecendo:**
1. Clique em **Simulation** (canto inferior direito).
2. No PC-Sala, faça `ping 203.0.113.10`.
3. Clique em **Capture/Forward** até o pacote passar pelo Roteador-Casa.
4. Clique no envelope do pacote **antes** e **depois** do roteador. Antes, o IP de origem é 192.168.0.1xx. Depois, é **200.10.10.2**. Isso é o NAT trocando o endereço.

No **ISP** (aba CLI):
```
show ip dhcp binding
```
Mostra que a operadora entregou o 200.10.10.2 para a sua casa.

**Prints sugeridos:** topologia completa, `ipconfig` + pings, site abrindo no notebook, NAT no modo simulação, celular com senha errada sem conexão.

Salve o arquivo como `rede-domestica.pkt` nesta pasta.

---

## Desafio extra (opcional): colocar um modem a cabo

Para ficar igual a uma casa de verdade, coloque um **Cable Modem** entre a operadora e o roteador:

1. Adicione uma **Cloud** (*Network Devices → WAN Emulation*) e um **Cable Modem** (*Network Devices → WAN Emulation*).
2. Ligue: ISP G0/0 → Cloud **Ethernet6** (cabo de cobre) · Cloud **Coax7** → Cable Modem **Port 0** (cabo **coaxial**) · Cable Modem **Port 1** → Roteador-Casa **Internet** (cabo de cobre).
3. Na Cloud → Config → **Cable**: ligue `Coax7` com `Ethernet6` → **Add**.

O modem é "transparente": todos os testes devem continuar funcionando igual.
