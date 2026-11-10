# Passo a passo · Análise de tráfego com Wireshark

Tempo estimado: **1 a 2 horas**. Você vai precisar de: **Wireshark** e **Python** (já instalado neste PC, comando `py`).

> ⚠️ Faça tudo **na sua rede, nos seus aparelhos**. Nunca capture o tráfego de outras pessoas.

---

## Preparação

1. Instale o Wireshark ([wireshark.org](https://www.wireshark.org/download.html)). Na instalação do **Npcap**, deixe marcada a opção **"Support loopback traffic"**.
2. Abra o Wireshark. Na tela inicial aparecem as **interfaces**:
   - **Wi-Fi** ou **Ethernet**: a sua conexão real.
   - **Adapter for loopback traffic capture**: o tráfego que fica dentro do próprio PC (usado no experimento 1).
3. Para iniciar uma captura, dê dois cliques na interface. Para parar, clique no **quadrado vermelho** ⏹.
4. O **filtro** é a barra verde no topo. Digite o filtro e tecle Enter.

---

## Experimento 1 · Senha legível no HTTP

1. Abra um terminal **nesta pasta** e rode:
   ```bash
   py servidor_login_inseguro.py
   ```
2. No Wireshark, comece a capturar na interface **Adapter for loopback traffic capture**.
3. No navegador, abra `http://127.0.0.1:8080`. A página já vem com dados **inventados** (`aluno.teste` / `SenhaFalsa123`). Clique em **Entrar**.
4. Pare a captura e use o filtro:
   ```
   http.request.method == "POST"
   ```
5. Clique no pacote `POST /login`. Na parte de baixo, abra **HTML Form URL Encoded**: o usuário e a senha estão lá, **em texto puro**.
6. Melhor ainda: botão direito no pacote → **Follow → HTTP Stream**. Aparece a conversa inteira, como um atacante veria.

📸 **Print:** a janela do Follow HTTP Stream com a senha destacada.

> **Variação (mais realista):** rode `py servidor_login_inseguro.py --rede`, capture na interface **Wi-Fi** e abra o endereço que o programa mostrar **pelo seu celular**, conectado na mesma rede. É exatamente o que aconteceria num Wi-Fi público. O Windows pode perguntar se libera o Python no firewall; libere só para **redes privadas**.

Para parar o servidor: **Ctrl+C** no terminal.

---

## Experimento 2 · HTTPS embaralhado

1. Capture na interface **Wi-Fi** (ou Ethernet).
2. Abra um site com cadeado, por exemplo `https://www.wikipedia.org`.
3. Pare e filtre:
   ```
   tls
   ```
4. Veja os pacotes **Application Data**: o conteúdo é só um monte de bytes sem sentido. É a criptografia funcionando.
5. Agora filtre:
   ```
   tls.handshake.extensions_server_name
   ```
   Clique no pacote **Client Hello** → abra *Transport Layer Security → Handshake → Extension: server_name*. O **nome do site** aparece. É isso que ainda "vaza" no HTTPS.

📸 **Prints:** os pacotes Application Data e o campo server_name.

---

## Experimento 3 · DNS

1. Capture na **Wi-Fi**.
2. No terminal:
   ```bash
   ipconfig /flushdns
   ```
   ```bash
   nslookup www.google.com
   ```
3. Filtre `dns`. Você verá a **pergunta** (*Standard query A www.google.com*) e a **resposta** com o IP.

📸 **Print:** pergunta e resposta, com o IP destacado.

---

## Experimento 4 · DHCP (o "DORA")

Quando um aparelho entra na rede, ele conversa com o roteador em 4 passos:

| Passo | Mensagem | Em português |
|---|---|---|
| **D** | Discover | "Tem algum servidor DHCP aí?" |
| **O** | Offer | "Tenho! Pode usar este IP." |
| **R** | Request | "Quero esse IP, por favor." |
| **A** | ACK | "Confirmado, é seu." |

1. Capture na **Wi-Fi** e filtre `dhcp`.
2. No terminal (a internet cai por alguns segundos):
   ```bash
   ipconfig /release
   ```
   ```bash
   ipconfig /renew
   ```
3. Procure as mensagens. No Windows, como o PC já conhece o roteador, às vezes aparecem só **Request** e **ACK**. Isso também é normal: ele pula a "procura".

📸 **Print:** as mensagens DHCP com o IP oferecido.

---

## Experimento 5 · ARP e ping (ICMP)

1. Descubra o IP do seu roteador: `ipconfig` → linha **Gateway Padrão** (geralmente `192.168.0.1` ou `192.168.1.1`).
2. Capture na **Wi-Fi**. No terminal:
   ```bash
   arp -d
   ```
   (se pedir permissão de administrador e você não tiver, pule este comando)
   ```bash
   ping 192.168.0.1
   ```
   (troque pelo IP do seu roteador)
3. Filtre:
   ```
   arp || icmp
   ```
4. Primeiro aparece o **ARP**: "Quem tem o IP 192.168.0.1? Responda para mim". O roteador responde com o seu **endereço MAC** (físico). Depois vêm os pings: **Echo request** e **Echo reply**.

📸 **Print:** o ARP seguido dos pings.

---

## Experimento 6 · Handshake TCP

1. Capture na **Wi-Fi**, abra qualquer site e pare.
2. Filtre:
   ```
   tcp.flags.syn == 1
   ```
3. Você verá pares **SYN** (o PC pede para conversar) e **SYN, ACK** (o servidor aceita).
4. Para ver os três passos juntos, clique num pacote **SYN**, olhe o número do campo *Stream index* (em *Transmission Control Protocol*) e filtre por ele, por exemplo:
   ```
   tcp.stream eq 5
   ```
   Os três primeiros pacotes são **SYN → SYN, ACK → ACK**. Só depois disso os dados começam a passar.

📸 **Print:** os três pacotes do handshake.

---

## Para o portfólio

1. Crie a pasta `prints/` aqui e salve os prints com os nomes sugeridos no README.
2. No README, troque o comentário `<!-- ... -->` pelas imagens.
3. **Cuidado com os prints:** apague ou borre IPs públicos, nomes de redes Wi-Fi e endereços MAC reais antes de publicar.
