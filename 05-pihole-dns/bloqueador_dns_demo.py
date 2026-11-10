"""Mini bloqueador DNS (mesma ideia do Pi-hole), para demonstrar o conceito sem Docker.
Responde 0.0.0.0 para dominios de anuncio e repassa o resto para 1.1.1.1.
NAO substitui o Pi-hole: tem uma lista de bloqueio minima e so atende este PC (127.0.0.1).

Uso:
    py bloqueador_dns_demo.py                 (Ctrl+C para parar)
    py bloqueador_dns_demo.py --segundos 30   (desliga sozinho)
Em outro terminal:
    powershell -ExecutionPolicy Bypass -File .\\testar-pihole.ps1 -Servidor 127.0.0.1
"""
import argparse, socket, struct, threading, time

BLOQUEIO = {"doubleclick.net", "googleadservices.com", "adservice.google.com",
            "googlesyndication.com", "ads.yahoo.com"}
UPSTREAM = ("1.1.1.1", 53)
stats = {"total": 0, "bloqueadas": 0}
trava = threading.Lock()


def ler_pergunta(dados):
    i, partes = 12, []
    while dados[i]:
        n = dados[i]
        partes.append(dados[i + 1:i + 1 + n].decode("ascii", "replace"))
        i += 1 + n
    qtipo = struct.unpack(">H", dados[i + 1:i + 3])[0]
    return ".".join(partes).lower(), qtipo, i + 5  # fim da pergunta


def esta_bloqueado(nome):
    partes = nome.split(".")
    return any(".".join(partes[k:]) in BLOQUEIO for k in range(len(partes)))


def resposta_bloqueada(dados, fim, qtipo):
    tem_resposta = qtipo == 1  # A -> 0.0.0.0 ; outros tipos -> sem resposta
    cab = dados[:2] + struct.pack(">HHHHH", 0x8180, 1, int(tem_resposta), 0, 0)
    corpo = dados[12:fim]
    if tem_resposta:
        corpo += b"\xc0\x0c" + struct.pack(">HHIH", 1, 1, 60, 4) + bytes(4)
    return cab + corpo


def atender(sock, dados, cliente):
    try:
        nome, qtipo, fim = ler_pergunta(dados)
    except (IndexError, struct.error):
        return
    bloq = esta_bloqueado(nome)
    with trava:
        stats["total"] += 1
        stats["bloqueadas"] += bloq
    tipo = {1: "A", 28: "AAAA"}.get(qtipo, str(qtipo))
    if bloq:
        sock.sendto(resposta_bloqueada(dados, fim, qtipo), cliente)
        print(f"  BLOQUEADO  {tipo:<4} {nome}", flush=True)
        return
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as up:
        up.settimeout(3)
        try:
            up.sendto(dados, UPSTREAM)
            sock.sendto(up.recv(4096), cliente)
            print(f"  liberado   {tipo:<4} {nome}", flush=True)
        except OSError:
            print(f"  ERRO       {tipo:<4} {nome} (sem resposta do 1.1.1.1)", flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--segundos", type=int, default=0, help="desliga sozinho depois de N segundos")
    args = ap.parse_args()
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("127.0.0.1", 53))
    sock.settimeout(1)
    print("Bloqueador DNS ouvindo em 127.0.0.1:53\n", flush=True)
    limite = time.time() + args.segundos if args.segundos else None
    while not limite or time.time() < limite:
        try:
            dados, cliente = sock.recvfrom(4096)
        except socket.timeout:
            continue
        threading.Thread(target=atender, args=(sock, dados, cliente), daemon=True).start()
    time.sleep(1)
    t, b = stats["total"], stats["bloqueadas"]
    print(f"\nResumo: {t} consultas, {b} bloqueadas ({(b / t * 100 if t else 0):.0f}%)", flush=True)


if __name__ == "__main__":
    main()
