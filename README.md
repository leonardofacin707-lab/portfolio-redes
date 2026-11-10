# Portfólio de Redes de Computadores

Projetos práticos de redes, do básico ao intermediário, montados para estudo e para demonstrar habilidades de **suporte técnico, NOC e analista de redes**.

Cada projeto parte de um **problema real**, mostra a **solução** (topologia, endereçamento e configurações) e termina com **testes que provam que funciona**.

> **Status:** em andamento. Configurações e roteiros prontos; as capturas de tela de cada teste entram à medida que executo cada laboratório.

| # | Projeto | Nível | Ferramentas | O que demonstra |
|---|---|---|---|---|
| 01 | [Rede doméstica (SOHO)](01-rede-domestica-soho/) | 🟢 Iniciante | Cisco Packet Tracer | LAN x WAN, Wi-Fi WPA2, DHCP, NAT, DNS, boas práticas de segurança |
| 02 | [Análise de tráfego com Wireshark](02-analise-trafego-wireshark/) | 🟢 Iniciante | Wireshark, Python | HTTP x HTTPS, DNS, DHCP, ARP, ICMP, handshake TCP |
| 03 | [Rede corporativa com VLANs](03-rede-corporativa-vlans/) | 🟡 Intermediário | Cisco Packet Tracer | VLANs, trunk 802.1Q, roteamento entre VLANs, DHCP, ACLs, SSH |
| 04 | [WAN matriz e filiais com OSPF](04-wan-ospf-redundancia/) | 🟡 Intermediário | Cisco Packet Tracer | OSPF, redundância de links, autenticação OSPF, sub-redes /30 |
| 05 | [Bloqueador de anúncios para a rede (Pi-hole)](05-pihole-dns/) | 🔴 Avançado | Docker / Raspberry Pi, PowerShell | DNS, servidor Linux, contêineres, automação de testes |

## Habilidades

- **Fundamentos:** modelo cliente-servidor, LAN/WAN, dispositivos finais e intermediários, endereçamento IPv4 e sub-redes
- **Switching:** VLANs, trunks 802.1Q, portas de acesso, desligamento de portas não usadas
- **Roteamento:** roteamento entre VLANs (router-on-a-stick), OSPF de área única, custo de rotas, convergência
- **Serviços:** DHCP, DNS, NAT, HTTP
- **Segurança:** WPA2, ACLs estendidas, SSH no lugar de Telnet, autenticação OSPF MD5, filtragem DNS
- **Análise:** captura e leitura de pacotes no Wireshark
- **Automação:** scripts em Python e PowerShell

## Estrutura de cada projeto

```
NN-nome-do-projeto/
├── README.md          → problema, solução, topologia, testes (a "vitrine")
├── PASSO-A-PASSO.md   → como montar do zero
└── configs/           → configurações prontas dos equipamentos
```

> As senhas que aparecem nas configurações são **apenas de laboratório**. Em um ambiente real, cada equipamento teria senhas fortes e únicas, guardadas em um cofre de senhas.

---

**Autor:** Leonardo Facin · [GitHub](https://github.com/leonardofacin707-lab) · Estudante de redes (Cisco Networking Academy)
