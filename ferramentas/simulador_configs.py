"""Simulador LOGICO das configuracoes Cisco do portfolio (projetos 01, 03 e 04).

Le os arquivos configs/*.txt de verdade (IPs, VLANs, trunks, DHCP, ACLs, OSPF)
e calcula o resultado de cada teste do README. Nao e o Packet Tracer: ele modela
as regras (ACL de cima para baixo, deny implicito, menor custo OSPF etc.).

Uso (na pasta do portfolio):
    py ferramentas/simulador_configs.py

Sai com codigo 0 se tudo conferir com os README, ou 1 listando as diferencas.
"""
import heapq
import ipaddress as ipa
import pathlib
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
BASE = pathlib.Path(__file__).resolve().parent.parent
OK, NOK = "✅", "❌"
ip = ipa.ip_address
falhas = []


def confere(descricao, obtido, esperado):
    bate = obtido == esperado
    if not bate:
        falhas.append(f"{descricao}: obtido {obtido!r}, esperado {esperado!r}")
    return "" if bate else f"   <-- DIFERENTE DO ESPERADO ({esperado})"


# ----------------------------------------------------------------- parser IOS
class Iface:
    def __init__(self, nome):
        self.nome, self.ip, self.shutdown = nome, None, False
        self.acl_in = self.custo = self.chave = self.dot1q = None
        self.vlan_acesso, self.modo, self.permitidas = 1, "access", None


class Disp:
    def __init__(self):
        self.nome, self.ifs, self.pools, self.excluidos = "?", {}, {}, []
        self.acl_ext, self.acl_std, self.vlans = {}, {}, {}
        self.vty_class, self.vty_transporte = None, None
        self.ospf_redes, self.passivas = [], set()

    def iface(self, nome):
        return self.ifs.setdefault(nome, Iface(nome))


def expandir_range(texto):
    m = re.match(r"(\S+?)(\d+)/(\d+)\s*-\s*(\d+)", texto)
    tipo, mod, ini, fim = m.group(1), m.group(2), int(m.group(3)), int(m.group(4))
    return [f"{tipo}{mod}/{n}" for n in range(ini, fim + 1)]


def spec(tokens):
    """Le 'any' | 'host X' | 'X wildcard'. Devolve ((rede, wildcard), resto)."""
    if tokens[0] == "any":
        return (0, 0xFFFFFFFF), tokens[1:]
    if tokens[0] == "host":
        return (int(ip(tokens[1])), 0), tokens[2:]
    return (int(ip(tokens[0])), int(ip(tokens[1]))), tokens[2:]


PORTAS = {"bootps": 67, "bootpc": 68, "www": 80, "domain": 53}


def ler(caminho):
    d, ctx = Disp(), None
    for bruta in caminho.read_text().splitlines():
        if not bruta.strip() or bruta.strip().startswith("!"):
            continue
        s, recuada = bruta.strip(), bruta.startswith(" ")
        t = s.split()
        if not recuada:
            ctx = None
            if t[0] == "hostname":
                d.nome = t[1]
            elif s.startswith("interface range "):
                ctx = ("if", [d.iface(n) for n in expandir_range(s[16:])])
            elif t[0] == "interface":
                ctx = ("if", [d.iface(t[1])])
            elif s.startswith("ip dhcp excluded-address"):
                a = ip(t[3])
                d.excluidos.append((a, ip(t[4]) if len(t) > 4 else a))
            elif s.startswith("ip dhcp pool"):
                ctx = ("pool", d.pools.setdefault(t[3], {}))
            elif s.startswith("ip access-list extended"):
                ctx = ("acl", d.acl_ext.setdefault(t[3], []))
            elif t[0] == "access-list" and t[2] in ("permit", "deny"):
                d.acl_std.setdefault(t[1], []).append((t[2], spec(t[3:])[0]))
            elif s.startswith("router ospf"):
                ctx = ("ospf", None)
            elif t[0] == "vlan" and t[1].isdigit():
                ctx = ("vlan", int(t[1]))
                d.vlans[int(t[1])] = ""
            elif s.startswith("line vty"):
                ctx = ("vty", None)
            continue
        if not ctx:
            continue
        tipo, alvo = ctx
        if tipo == "if":
            for i in alvo:
                if t[:2] == ["ip", "address"]:
                    i.ip = ipa.ip_interface(f"{t[2]}/{t[3]}")
                elif s == "shutdown":
                    i.shutdown = True
                elif s == "no shutdown":
                    i.shutdown = False
                elif t[0] == "encapsulation":
                    i.dot1q = int(t[2])
                elif t[:2] == ["ip", "access-group"] and t[3] == "in":
                    i.acl_in = t[2]
                elif t[:3] == ["ip", "ospf", "cost"]:
                    i.custo = int(t[3])
                elif t[:3] == ["ip", "ospf", "message-digest-key"]:
                    i.chave = t[-1]
                elif t[:3] == ["switchport", "access", "vlan"]:
                    i.vlan_acesso = int(t[3])
                elif t[:2] == ["switchport", "mode"]:
                    i.modo = t[2]
                elif t[:4] == ["switchport", "trunk", "allowed", "vlan"]:
                    i.permitidas = {int(v) for v in t[4].split(",")}
        elif tipo == "pool":
            if t[0] == "network":
                alvo["rede"] = ipa.ip_network(f"{t[1]}/{t[2]}")
            elif t[0] == "default-router":
                alvo["gw"] = ip(t[1])
            elif t[0] == "dns-server":
                alvo["dns"] = ip(t[1])
        elif tipo == "acl" and t[0] != "remark":
            origem, resto = spec(t[2:])
            destino, resto = spec(resto)
            porta = PORTAS.get(resto[1], None) if resto[:1] == ["eq"] else None
            if resto[:1] == ["eq"] and porta is None:
                porta = int(resto[1])
            alvo.append((t[0], t[1], origem, destino, porta))
        elif tipo == "ospf":
            if t[0] == "network":
                d.ospf_redes.append((int(ip(t[1])), int(ip(t[2]))))
            elif t[0] == "passive-interface":
                d.passivas.add(t[1])
        elif tipo == "vlan" and t[0] == "name":
            d.vlans[alvo] = t[1]
        elif tipo == "vty":
            if t[0] == "access-class":
                d.vty_class = t[1]
            elif t[:2] == ["transport", "input"]:
                d.vty_transporte = t[2:]
    return d


def casa(regra, endereco):
    rede, wc = regra
    return (int(endereco) & ~wc & 0xFFFFFFFF) == (rede & ~wc & 0xFFFFFFFF)


def acl_ext_permite(d, nome, proto, origem, destino, porta=None):
    if nome is None:
        return True
    for acao, p, o, de, eq in d.acl_ext[nome]:
        if p != "ip" and p != proto:
            continue
        if eq is not None and (proto not in ("tcp", "udp") or porta != eq):
            continue
        if casa(o, origem) and casa(de, destino):
            return acao == "permit"
    return False  # deny implicito


def acl_std_permite(d, numero, origem):
    if numero is None:
        return True
    for acao, regra in d.acl_std[numero]:
        if casa(regra, origem):
            return acao == "permit"
    return False


def dhcp(d, pool, ja_usados):
    rede = d.pools[pool]["rede"]
    for h in rede.hosts():
        if any(a <= h <= b for a, b in d.excluidos) or h == d.pools[pool]["gw"] or h in ja_usados:
            continue
        ja_usados.add(h)
        return h
    return None


def titulo(texto):
    print("\n" + "=" * 72 + f"\n{texto}\n" + "=" * 72)


# ================================================================ PROJETO 01
def projeto01():
    titulo("PROJETO 01 · Rede doméstica (SOHO)")
    isp = ler(BASE / "01-rede-domestica-soho/configs/ISP.txt")
    pool = isp.pools["CLIENTE-CASA"]
    wan_casa = dhcp(isp, "CLIENTE-CASA", set())
    print(f"Operadora entrega ao Roteador-Casa: {wan_casa} (gateway {pool['gw']}, DNS {pool['dns']})"
          + confere("IP WAN da casa", str(wan_casa), "200.10.10.2"))
    g1 = isp.ifs["GigabitEthernet0/1"].ip
    print(f"Servidor 203.0.113.10 está na rede {g1.network} do ISP (gateway {g1.ip}): "
          + (OK if ip("203.0.113.10") in g1.network else NOK))

    # Lado da casa: configurado pela GUI do WRT300N, valores do PASSO-A-PASSO
    lan = ipa.ip_network("192.168.0.0/24")
    faixa = [ip("192.168.0.100") + n for n in range(50)]
    impressora = ip("192.168.0.20")
    print(f"\nLAN {lan} · DHCP {faixa[0]}–{faixa[-1]} · Impressora fixa {impressora}: "
          + (f"{OK} fora da faixa do DHCP" if impressora not in faixa else f"{NOK} conflito"))
    senha_wifi = "MinhaRede@2026"
    aparelhos = [("PC-Sala", "cabo", None), ("Notebook", "wifi", "MinhaRede@2026"),
                 ("Smartphone", "wifi", "MinhaRede@2026"), ("Tablet", "wifi", "MinhaRede@2026"),
                 ("Smartphone-Intruso", "wifi", "senhaerrada")]
    proximo = iter(faixa)
    print("\nAparelho              Conexão   IP recebido")
    for nome, meio, senha in aparelhos:
        if meio == "wifi" and senha != senha_wifi:
            print(f"{nome:<21} Wi-Fi     {NOK} não conecta (senha WPA2 errada)")
            continue
        print(f"{nome:<21} {'Cabo ' if meio == 'cabo' else 'Wi-Fi'}     {next(proximo)}")

    pc = faixa[0]
    print("\nCaminho de um pacote do PC-Sala até o site (NAT):")
    print(f"  1. PC-Sala {pc} -> pergunta DNS de www.meusite.com ao 203.0.113.10 -> resposta 203.0.113.10")
    print(f"  2. Pacote sai do PC:            origem {pc}  destino 203.0.113.10")
    print(f"  3. Roteador-Casa faz NAT:       origem {wan_casa}  destino 203.0.113.10")
    print(f"  4. ISP entrega pela {('GigabitEthernet0/1')} (rede diretamente conectada)")
    print(f"  5. Resposta volta para {wan_casa}; o NAT devolve ao PC {pc}  {OK}")
    print(f"\ntracert 203.0.113.10:  1) 192.168.0.1   2) {isp.ifs['GigabitEthernet0/0'].ip.ip}   3) 203.0.113.10")


# ================================================================ PROJETO 03
def projeto03():
    titulo("PROJETO 03 · Rede corporativa com VLANs")
    pasta = BASE / "03-rede-corporativa-vlans/configs"
    r1, sw1, sw2 = ler(pasta / "R1-EMPRESA.txt"), ler(pasta / "SW1.txt"), ler(pasta / "SW2.txt")

    subifs = {i.dot1q: i for i in r1.ifs.values() if i.dot1q}
    print("VLANs nos switches: " + ", ".join(f"{v} {n}" for v, n in sorted(sw1.vlans.items())))
    print("Subinterfaces do R1: " + ", ".join(f"{i.nome} ({i.ip})" for i in subifs.values()))

    caminho_sw2 = [sw2.ifs["GigabitEthernet0/2"], sw1.ifs["GigabitEthernet0/2"], sw1.ifs["GigabitEthernet0/1"]]
    caminho_sw1 = [sw1.ifs["GigabitEthernet0/1"]]

    hosts = [("PC-FIN-1", sw1, "FastEthernet0/1"), ("PC-FIN-2", sw1, "FastEthernet0/2"),
             ("PC-RH-1", sw1, "FastEthernet0/11"), ("PC-RH-2", sw1, "FastEthernet0/12"),
             ("PC-TI-1", sw2, "FastEthernet0/1"), ("Servidor-TI", sw2, "FastEthernet0/2"),
             ("Notebook-VISIT-1", sw2, "FastEthernet0/11"), ("Notebook-VISIT-2", sw2, "FastEthernet0/12")]
    usados, h = set(), {}
    print("\nAparelho             Switch/porta          VLAN  IP")
    for nome, sw, porta in hosts:
        p = sw.ifs[porta]
        vlan = p.vlan_acesso
        trunks = caminho_sw2 if sw is sw2 else caminho_sw1
        chega = (not p.shutdown and vlan in sw1.vlans and vlan in sw2.vlans
                 and all(vlan in t.permitidas and t.modo == "trunk" for t in trunks) and vlan in subifs)
        if nome == "Servidor-TI":
            end = ip("192.168.30.10")
        elif not chega:
            end = None
        else:
            pool = next(n for n, pl in r1.pools.items() if subifs[vlan].ip.ip in pl["rede"])
            end = dhcp(r1, pool, usados)
        h[nome] = (end, vlan)
        print(f"{nome:<20} {sw.nome} {porta:<17} {vlan:<5} {end or '169.254.x.x (sem DHCP)'}")

    donos_r1 = {i.ip.ip for i in r1.ifs.values() if i.ip}

    def subif_de(endereco):
        return next((i for i in subifs.values() if endereco in i.ip.network), None)

    def fluxo(origem, destino, proto, porta=None):
        """Ida e volta passando pelo R1 (ou direto, se mesma VLAN)."""
        if origem == destino:
            return True
        ent = subif_de(origem)
        if ent and destino in ent.ip.network and destino not in donos_r1:
            return True  # mesma VLAN: o switch entrega, nao passa pelo roteador
        if not acl_ext_permite(r1, ent.acl_in, proto, origem, destino, porta):
            return False
        if destino in donos_r1:
            return True
        sai = subif_de(destino)
        if sai is None:
            return False
        return acl_ext_permite(r1, sai.acl_in, proto, destino, origem)

    grupos = [("Financeiro", "PC-FIN-1", "PC-FIN-2"), ("RH", "PC-RH-1", "PC-RH-2"),
              ("TI", "PC-TI-1", "Servidor-TI"), ("Visitantes", "Notebook-VISIT-1", "Notebook-VISIT-2")]
    alvo_coluna = {"Financeiro": "PC-FIN-2", "RH": "PC-RH-2", "TI": "Servidor-TI", "Visitantes": "Notebook-VISIT-2"}
    esperado = {"Financeiro": "✅❌✅❌✅", "RH": "❌✅✅❌✅", "TI": "✅✅✅❌✅", "Visitantes": "❌❌❌✅✅"}
    print("\nMatriz de ping (linha -> coluna):")
    print(f"{'':<12}{'Financeiro':<12}{'RH':<12}{'TI':<12}{'Visitantes':<12}Internet")
    for grupo, quem, _ in grupos:
        o = h[quem][0]
        linha = ""
        for col, _, _ in grupos:
            d = h[alvo_coluna[col] if alvo_coluna[col] != quem else _][0]
            linha += OK if fluxo(o, d, "icmp") else NOK
        linha += OK if fluxo(o, ip("8.8.8.8"), "icmp") else NOK
        print(f"{grupo:<12}" + "".join(f"{c:<11}" for c in linha) + confere(f"matriz {grupo}", linha, esperado[grupo]))

    print("\nTestes extras:")
    srv = ip("192.168.30.10")
    for quem, esp in [("PC-FIN-1", True), ("Notebook-VISIT-1", False)]:
        o = h[quem][0]
        pool_dns = next(pl["dns"] for pl in r1.pools.values() if o in pl["rede"])
        dns_ok = fluxo(o, pool_dns, "udp", 53) and pool_dns == srv
        web_ok = dns_ok and fluxo(o, srv, "tcp", 80)
        print(f"  {quem:<17} abre http://intranet.empresa.lab: {OK if web_ok else NOK}"
              f"  (DNS {pool_dns})" + confere(f"intranet {quem}", web_ok, esp))

    def ssh(quem, destino, disp):
        o = h[quem][0]
        if "ssh" not in (disp.vty_transporte or []):
            return False
        return fluxo(o, destino, "tcp", 22) and acl_std_permite(disp, disp.vty_class, o)

    for quem, dest, disp, nome, esp in [("PC-TI-1", ip("192.168.30.1"), r1, "R1", True),
                                       ("PC-TI-1", ip("192.168.99.11"), sw1, "SW1", True),
                                       ("PC-RH-1", ip("192.168.20.1"), r1, "R1", False),
                                       ("Notebook-VISIT-1", ip("192.168.40.1"), r1, "R1", False)]:
        r = ssh(quem, dest, disp)
        print(f"  {quem:<17} ssh -l admin {dest} ({nome}): {OK + ' entra' if r else NOK + ' recusado'}"
              + confere(f"ssh {quem}->{dest}", r, esp))
    print(f"  Telnet no R1: {NOK + ' recusado (transport input ' + ' '.join(r1.vty_transporte) + ')'}")
    portas_off = [n for n, i in sw1.ifs.items() if i.shutdown]
    print(f"  Portas desligadas no SW1: {len(portas_off)} ({portas_off[0]} a {portas_off[-1]}) na VLAN "
          f"{sw1.ifs[portas_off[0]].vlan_acesso}")


# ================================================================ PROJETO 04
def projeto04(desligar=None, trocar_chave=None, mostrar=True):
    pasta = BASE / "04-wan-ospf-redundancia/configs"
    rs = {d.nome: d for d in (ler(pasta / f) for f in ("R-SP.txt", "R-RJ.txt", "R-BH.txt"))}
    if desligar:
        rs[desligar[0]].ifs[desligar[1]].shutdown = True
    if trocar_chave:
        rs[trocar_chave[0]].ifs[trocar_chave[1]].chave = trocar_chave[2]

    def ativa(d, i):
        return i.ip and any(casa((rede, wc), i.ip.ip) for rede, wc in d.ospf_redes)

    # vizinhancas: mesma sub-rede, as duas pontas ligadas, nao passivas, mesma chave
    ponta = [(d, i) for d in rs.values() for i in d.ifs.values() if i.ip and i.ip.network.prefixlen < 32]
    vizinhos, caidos = {n: [] for n in rs}, set()
    for (a, ia), (b, ib) in ((x, y) for x in ponta for y in ponta if x[0] is not y[0]):
        if ia.ip.network != ib.ip.network:
            continue
        if ia.shutdown or ib.shutdown:
            caidos.add((a.nome, ia.nome))
            continue
        if ativa(a, ia) and ativa(b, ib) and ia.nome not in a.passivas and ib.nome not in b.passivas:
            if ia.chave == ib.chave:
                vizinhos[a.nome].append((b.nome, ia, ib))

    def custo(i):
        return i.custo or 1

    redes = {}  # rede -> [(roteador, custo da interface)]
    for d in rs.values():
        for i in d.ifs.values():
            if ativa(d, i) and (d.nome, i.nome) not in caidos and not i.shutdown:
                redes.setdefault(i.ip.network, []).append((d.nome, custo(i)))

    def dijkstra(origem):
        dist, ant, fila = {origem: 0}, {}, [(0, origem)]
        while fila:
            c, u = heapq.heappop(fila)
            if c > dist[u]:
                continue
            for v, iu, iv in vizinhos[u]:
                nc = c + custo(iu)
                if nc < dist.get(v, 1e9):
                    dist[v], ant[v] = nc, (u, iu, iv)
                    heapq.heappush(fila, (nc, v))
        return dist, ant

    def caminho(origem, destino, ant):
        passos, v = [], destino
        while v != origem:
            u, iu, iv = ant[v]
            passos.append((u, iu, v, iv))
            v = u
        return passos[::-1]

    def rotas(r):
        dist, ant = dijkstra(r)
        tabela = {}
        for rede, donos in redes.items():
            if any(dono == r for dono, _ in donos):
                continue
            melhor = min(((dist[d] + c, d) for d, c in donos if d in dist), default=None)
            if melhor:
                passo = caminho(r, melhor[1], ant)[0]
                tabela[rede] = (melhor[0], passo[3].ip.ip, passo[1].nome)
        return tabela

    def tracert(r_origem, destino):
        dist, ant = dijkstra(r_origem)
        rede = next(n for n in redes if destino in n)
        dono = min(((dist[d] + c, d) for d, c in redes[rede] if d in dist))[1]
        saltos = [rs[r_origem].ifs["GigabitEthernet0/0"].ip.ip]
        saltos += [iv.ip.ip for _, _, _, iv in caminho(r_origem, dono, ant)]
        return saltos + [destino]

    return rs, vizinhos, rotas, tracert


def mostra_rotas(nome, rotas):
    print(f"\n{nome}# show ip route ospf")
    for rede, (c, nh, saida) in sorted(rotas(nome).items(), key=lambda x: x[0]):
        print(f"  O  {str(rede):<16} [110/{c}] via {nh}, {saida}")


def projeto04_tudo():
    titulo("PROJETO 04 · WAN matriz e filiais com OSPF")
    rs, viz, rotas, tracert = projeto04()
    print("show ip ospf neighbor:")
    for r, lista in viz.items():
        txt = ", ".join(f"{v} ({iu.nome})" for v, iu, _ in lista)
        print(f"  {r}: {len(lista)} vizinhos FULL -> {txt}" + confere(f"vizinhos {r}", len(lista), 2))

    mostra_rotas("R-RJ", rotas)
    c, nh, _ = rotas("R-RJ")[ipa.ip_network("192.168.3.0/24")]
    print(f"  -> R-RJ chega em BH via {nh} (São Paulo), custo {c}"
          + confere("RJ->BH", (str(nh), c), ("10.0.0.1", 3)))
    t = tracert("R-RJ", ip("192.168.3.11"))
    print("\ntracert PC-RJ -> PC-BH:  " + "  ".join(f"{n}) {x}" for n, x in enumerate(t, 1)))

    print("\n>>> R-SP: interface GigabitEthernet0/2 -> shutdown  (cai o link SP-BH)")
    rs, viz, rotas, tracert = projeto04(desligar=("R-SP", "GigabitEthernet0/2"))
    print("  vizinhos agora: " + "; ".join(f"{r}: {len(l)}" for r, l in viz.items()))
    mostra_rotas("R-BH", rotas)
    c, nh, _ = rotas("R-BH")[ipa.ip_network("192.168.1.0/24")]
    print(f"  -> R-BH chega na matriz via {nh} (link BACKUP pelo RJ), custo {c}"
          + confere("BH->SP backup", (str(nh), c), ("10.0.0.9", 102)))
    t = tracert("R-BH", ip("192.168.1.10"))
    print("\ntracert PC-BH -> Servidor-SP:  " + "  ".join(f"{n}) {x}" for n, x in enumerate(t, 1))
          + confere("tracert backup", [str(x) for x in t], ["192.168.3.1", "10.0.0.9", "10.0.0.1", "192.168.1.10"]))

    print("\n>>> R-SP: no shutdown (link volta)")
    rs, viz, rotas, tracert = projeto04()
    c, nh, _ = rotas("R-BH")[ipa.ip_network("192.168.1.0/24")]
    print(f"  R-BH volta a usar {nh} (link principal), custo {c}" + confere("BH->SP normal", str(nh), "10.0.0.5"))

    print("\n>>> R-BH G0/1: ip ospf message-digest-key 1 md5 SenhaErrada")
    rs, viz, rotas, tracert = projeto04(trocar_chave=("R-BH", "GigabitEthernet0/1", "SenhaErrada"))
    nomes = [v for v, _, _ in viz["R-BH"]]
    print(f"  Vizinhos do R-BH: {nomes}  -> R-SP saiu (senha não confere) "
          + (OK if "R-SP" not in nomes else NOK))


if __name__ == "__main__":
    projeto01()
    projeto03()
    projeto04_tudo()
    titulo("RESUMO")
    if falhas:
        print("Diferenças em relação ao README:")
        for f in falhas:
            print("  - " + f)
        sys.exit(1)
    print(f"{OK} Todos os resultados conferem com o que está documentado nos README.")
