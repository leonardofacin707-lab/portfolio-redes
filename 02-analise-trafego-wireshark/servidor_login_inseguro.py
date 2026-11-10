"""
Servidor de login INSEGURO (HTTP sem criptografia), feito para estudo no Wireshark.

Ele mostra uma pagina de login falsa. Quando voce envia o formulario, o usuario e a
senha viajam pela rede em texto puro, e o Wireshark consegue ler tudo.

Uso:
    py servidor_login_inseguro.py            -> so neste computador (http://127.0.0.1:8080)
    py servidor_login_inseguro.py --rede     -> tambem acessivel por outros aparelhos da sua rede local
    py servidor_login_inseguro.py --porta 9000

NUNCA digite senhas reais nesta pagina. Use dados inventados.
Para parar o servidor: Ctrl+C.
"""

import argparse
import html
import socket
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs

TAMANHO_MAXIMO_FORMULARIO = 10_000  # bytes

ESTILO = """
<style>
  body { font-family: system-ui, sans-serif; background: #f4f6f8; color: #1d2733;
         display: flex; justify-content: center; padding: 40px 16px; margin: 0; }
  main { background: #fff; max-width: 420px; width: 100%; padding: 28px;
         border-radius: 12px; box-shadow: 0 4px 18px rgba(0,0,0,.08); }
  .aviso { background: #fff4e5; border: 1px solid #f0b35b; padding: 10px 12px;
           border-radius: 8px; font-size: 14px; margin-bottom: 20px; }
  label { display: block; margin-top: 14px; font-weight: 600; }
  input { width: 100%; box-sizing: border-box; padding: 10px; margin-top: 6px;
          border: 1px solid #c7ced6; border-radius: 6px; font-size: 16px; }
  button { margin-top: 20px; width: 100%; padding: 12px; border: 0; border-radius: 6px;
           background: #1f6feb; color: #fff; font-size: 16px; cursor: pointer; }
</style>
"""

PAGINA_LOGIN = f"""<!doctype html>
<html lang="pt-BR">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Login de teste (HTTP)</title>{ESTILO}</head>
<body><main>
  <h1>Login de teste</h1>
  <p class="aviso">&#9888; Pagina de <strong>estudo</strong> sem criptografia (HTTP).
  Use apenas dados <strong>inventados</strong>.</p>
  <form method="post" action="/login">
    <label for="usuario">Usuario</label>
    <input id="usuario" name="usuario" autocomplete="off" value="aluno.teste">
    <label for="senha">Senha</label>
    <input id="senha" name="senha" type="password" autocomplete="off" value="SenhaFalsa123">
    <button type="submit">Entrar</button>
  </form>
</main></body></html>
"""

PAGINA_OK = f"""<!doctype html>
<html lang="pt-BR">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Login recebido</title>{ESTILO}</head>
<body><main>
  <h1>Login recebido, __USUARIO__</h1>
  <p>Agora va ao Wireshark e procure o pacote <code>POST /login</code>.
  O usuario e a senha estao la, legiveis, porque esta pagina usa HTTP.</p>
  <p><a href="/">Voltar</a></p>
</main></body></html>
"""


class TratadorLogin(BaseHTTPRequestHandler):
    server_version = "LoginInseguro/1.0"

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            self._responder(200, PAGINA_LOGIN)
        else:
            self._responder(404, "<h1>404 - pagina nao encontrada</h1>")

    def do_POST(self):
        if self.path != "/login":
            self._responder(404, "<h1>404 - pagina nao encontrada</h1>")
            return

        try:
            tamanho = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            self._responder(400, "<h1>400 - pedido invalido</h1>")
            return
        if tamanho < 0 or tamanho > TAMANHO_MAXIMO_FORMULARIO:
            self._responder(413, "<h1>413 - formulario grande demais</h1>")
            return

        corpo = self.rfile.read(tamanho).decode("utf-8", errors="replace")
        dados = parse_qs(corpo)
        usuario = dados.get("usuario", [""])[0] or "(vazio)"
        # A senha NAO e mostrada nem guardada aqui. O objetivo e ve-la no Wireshark.
        print(f"  -> formulario recebido do usuario '{usuario}' (veja a senha no Wireshark)")
        self._responder(200, PAGINA_OK.replace("__USUARIO__", html.escape(usuario)))

    def _responder(self, status, conteudo):
        dados = conteudo.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(dados)))
        self.end_headers()
        self.wfile.write(dados)

    def log_message(self, formato, *args):
        print(f"[{self.address_string()}] {formato % args}")


def ip_na_rede_local():
    """Descobre o IP deste PC na rede local (nenhum pacote e enviado de verdade)."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.connect(("192.0.2.1", 80))
        return sock.getsockname()[0]
    except OSError:
        return "SEU-IP"
    finally:
        sock.close()


def main():
    parser = argparse.ArgumentParser(description="Servidor de login HTTP inseguro, para estudo no Wireshark.")
    parser.add_argument("--rede", action="store_true",
                        help="aceita conexoes de outros aparelhos da rede local (padrao: so este PC)")
    parser.add_argument("--porta", type=int, default=8080, help="porta TCP (padrao: 8080)")
    args = parser.parse_args()

    endereco = "0.0.0.0" if args.rede else "127.0.0.1"
    servidor = ThreadingHTTPServer((endereco, args.porta), TratadorLogin)

    print("Servidor de login INSEGURO rodando (somente para estudo).")
    print(f"  Neste PC:        http://127.0.0.1:{args.porta}")
    if args.rede:
        print(f"  Outros aparelhos: http://{ip_na_rede_local()}:{args.porta}")
    print("  Use dados inventados. Ctrl+C para parar.\n")

    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor encerrado.")
    finally:
        servidor.server_close()


if __name__ == "__main__":
    main()
