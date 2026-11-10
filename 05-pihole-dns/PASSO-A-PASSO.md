# Passo a passo · Pi-hole

Tempo estimado: **1 hora**. Escolha **um** dos caminhos:

| Caminho | Precisa de | Bom para |
|---|---|---|
| **A · Docker no seu PC** | Docker Desktop | Testar hoje, sem comprar nada. Funciona só enquanto o PC estiver ligado |
| **B · Raspberry Pi** | Raspberry Pi + cartão SD | Deixar ligado 24h e proteger a casa toda |

---

## Caminho A · Docker no Windows

### 1. Instalar o Docker Desktop
Baixe em [docker.com](https://www.docker.com/products/docker-desktop/), instale e reinicie o PC. Abra o Docker Desktop e espere aparecer **"Engine running"**.

### 2. Criar a senha
Nesta pasta, copie o arquivo `.env.example` com o nome `.env`:

```powershell
Copy-Item .env.example .env
```

Abra o `.env` no Bloco de Notas e troque `troque-por-uma-senha-forte` por uma senha sua.

### 3. Subir o Pi-hole
Abra o terminal **nesta pasta** e rode:

```bash
docker compose up -d
```

Na primeira vez ele baixa a imagem (alguns minutos). Depois confira:

```bash
docker compose ps
```

O status deve ficar **healthy** depois de cerca de 1 minuto.

> **Erro "port 53 already in use"?** Algum programa do Windows já usa a porta de DNS (geralmente o *Compartilhamento de Conexão de Internet*). Feche esse serviço ou use o Caminho B.

### 4. Abrir o painel
No navegador: `http://localhost:8080/admin` → entre com a senha do `.env`.

### 5. Descobrir o IP do seu PC
```bash
ipconfig
```
Anote o **Endereço IPv4** da placa Wi-Fi ou Ethernet (ex.: `192.168.0.50`). Esse é o IP do Pi-hole.

### 6. Testar
Nesta pasta:

```powershell
powershell -ExecutionPolicy Bypass -File .\testar-pihole.ps1 -Servidor 127.0.0.1
```

Devem aparecer **7 de 7 testes OK**. 📸 Tire print.

### 7. Usar em um aparelho
No **celular** (conectado no mesmo Wi-Fi): configurações do Wi-Fi → sua rede → **IP estático / DNS** → DNS 1 = IP do seu PC (passo 5).

> Para outros aparelhos alcançarem o Pi-hole, o Firewall do Windows precisa liberar a porta **53**. Se o Windows perguntar, permita apenas em **redes privadas**.

Abra alguns sites no celular e veja as consultas aparecerem no painel em **Query Log**.

### Comandos úteis
```bash
docker compose logs -f pihole
```
```bash
docker compose down
```
```bash
docker compose pull
```
(o último atualiza a imagem; depois rode `docker compose up -d` de novo)

---

## Caminho B · Raspberry Pi (24h)

1. Grave o **Raspberry Pi OS Lite** no cartão com o **Raspberry Pi Imager**. Nas opções avançadas do Imager, ative o **SSH** e crie seu usuário.
2. Ligue o Pi **no cabo** de rede do roteador.
3. No painel do roteador, **reserve um IP fixo** para o Raspberry (DHCP reservation), por exemplo `192.168.0.2`.
4. Acesse por SSH do seu PC:
   ```bash
   ssh seu-usuario@192.168.0.2
   ```
5. Siga o instalador oficial em [docs.pi-hole.net](https://docs.pi-hole.net/main/basic-install/) **ou** instale o Docker no Pi e use o mesmo `docker-compose.yml` desta pasta (trocando a porta `8080:80` por `80:80`, se quiser).
6. No **roteador**, em DHCP, coloque o IP do Raspberry como **DNS primário**. Assim **todos** os aparelhos da casa passam a usar o Pi-hole automaticamente.

> ⚠️ Não coloque um DNS "reserva" (como 8.8.8.8) como secundário no roteador: os aparelhos usariam o reserva e o bloqueio falharia em parte. Se o Pi-hole cair, volte o DNS do roteador ao automático.

---

## Para o portfólio 📸

Prints sugeridos:
1. **Dashboard** do Pi-hole com o total de consultas e a porcentagem bloqueada (depois de algumas horas de uso fica mais bonito).
2. **Query Log** mostrando consultas bloqueadas (em vermelho).
3. **Resultado do script** `testar-pihole.ps1`.
4. **Antes e depois** de um site cheio de anúncios.

Antes de publicar, **borre** IPs públicos, nomes de aparelhos e qualquer site pessoal que apareça no log.

## Se algo der errado

| Sintoma | Verifique |
|---|---|
| `docker compose up` diz que falta `PIHOLE_SENHA` | O arquivo `.env` existe nesta pasta? |
| Script diz "servidor não respondeu" | Pi-hole está rodando (`docker compose ps`)? IP certo? Firewall liberando a porta 53? |
| Um site normal parou de funcionar | Painel → *Query Log* → ache o domínio bloqueado → **Allow** |
| Celular não usa o Pi-hole | O celular pode estar com "DNS privado" ligado (Android). Desative em Configurações → Rede → DNS privado |
