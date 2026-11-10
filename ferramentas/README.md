# Ferramentas de validação

Scripts que testam os projetos de forma automática e repetível.

| Script | Projeto | O que faz | Como rodar |
|---|---|---|---|
| [simulador_configs.py](simulador_configs.py) | 01, 03, 04 | Lê as configurações Cisco (`configs/*.txt`) e calcula o resultado de cada teste: DHCP, matriz de ping com ACLs, SSH, vizinhos e rotas OSPF, falha de link e autenticação. Compara com o que os README prometem | `py ferramentas/simulador_configs.py` |
| [captura_automatica.ps1](../02-analise-trafego-wireshark/captura_automatica.ps1) | 02 | Captura real com o **tshark**: senha legível no HTTP, handshake TCP, DNS e o que fica visível no HTTPS | `powershell -ExecutionPolicy Bypass -File 02-analise-trafego-wireshark/captura_automatica.ps1 -Interface Wi-Fi` |
| [bloqueador_dns_demo.py](../05-pihole-dns/bloqueador_dns_demo.py) | 05 | Mini servidor DNS que bloqueia domínios de anúncio, para demonstrar o conceito do Pi-hole sem Docker | `py 05-pihole-dns/bloqueador_dns_demo.py` |
| [testar-pihole.ps1](../05-pihole-dns/testar-pihole.ps1) | 05 | Pergunta a um servidor DNS por domínios de anúncio e sites normais e confere o bloqueio | `powershell -ExecutionPolicy Bypass -File 05-pihole-dns/testar-pihole.ps1 -Servidor 127.0.0.1` |

## Sobre o simulador

O simulador é uma **validação lógica**, não substitui o Packet Tracer. Ele aplica as mesmas regras que os equipamentos aplicam:

- ACLs lidas **de cima para baixo**, com **deny implícito** no final, e verificadas na ida **e** na volta do pacote
- Tráfego na mesma VLAN não passa pelo roteador; entre VLANs, passa pela subinterface correspondente
- VLAN só chega ao roteador se existir nos dois switches e for permitida em todos os trunks do caminho
- OSPF: vizinhança só se as duas pontas estiverem ativas, não passivas e com a **mesma chave MD5**; rotas pelo **menor custo** (algoritmo de Dijkstra)

Se alguém alterar uma configuração e quebrar uma regra, o script aponta a diferença e sai com código 1.
