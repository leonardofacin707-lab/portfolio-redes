# Passo a passo · WAN com OSPF e redundância

Tempo estimado: **2 horas**. Ferramenta: **Cisco Packet Tracer**.

## Antes de começar: OSPF em 30 segundos

Sem OSPF, você teria que dizer a cada roteador, na mão, o caminho para cada rede (**rota estática**). Se um cabo cair, alguém precisa ir lá e mudar.

Com **OSPF**, os roteadores **conversam entre si** ("eu conheço a rede X, e o meu link até ela custa tanto"). Cada um monta sozinho o mapa da empresa e escolhe o **caminho mais barato**. Se um link cair, eles avisam uns aos outros e recalculam. É como um **GPS de trânsito** que desvia do engarrafamento sozinho.

---

## Parte 1 · Equipamentos

| Nome | Modelo |
|---|---|
| R-SP, R-RJ, R-BH | Router **2911** (já vem com 3 portas Gigabit: G0/0, G0/1, G0/2) |
| SW-SP, SW-RJ, SW-BH | Switch **2960** |
| PC-SP, PC-RJ, PC-BH | **PC** |
| Servidor-SP | **Server** |

Dica visual: desenhe um retângulo de cor diferente em volta de cada cidade (ferramenta de desenho da barra superior) e escreva o nome da cidade.

## Parte 2 · Cabos

| De | Porta | Para | Porta | Cabo |
|---|---|---|---|---|
| R-SP | G0/1 | R-RJ | G0/1 | **Copper Cross-Over** |
| R-SP | G0/2 | R-BH | G0/1 | **Copper Cross-Over** |
| R-RJ | G0/2 | R-BH | G0/2 | **Copper Cross-Over** |
| R-SP | G0/0 | SW-SP | G0/1 | Straight-Through |
| R-RJ | G0/0 | SW-RJ | G0/1 | Straight-Through |
| R-BH | G0/0 | SW-BH | G0/1 | Straight-Through |
| Servidor-SP | Fa0 | SW-SP | Fa0/1 | Straight-Through |
| PC-SP | Fa0 | SW-SP | Fa0/2 | Straight-Through |
| PC-RJ | Fa0 | SW-RJ | Fa0/1 | Straight-Through |
| PC-BH | Fa0 | SW-BH | Fa0/1 | Straight-Through |

> Roteador com roteador usa **cross-over**. Se usar o cabo errado, o link fica vermelho.

Os switches não precisam de configuração neste projeto.

## Parte 3 · Configurar os roteadores

Em cada roteador: **CLI** → Enter → cole o arquivo correspondente:
- R-SP → [configs/R-SP.txt](configs/R-SP.txt)
- R-RJ → [configs/R-RJ.txt](configs/R-RJ.txt)
- R-BH → [configs/R-BH.txt](configs/R-BH.txt)

Depois de configurar o segundo roteador, devem aparecer mensagens como:
```
%OSPF-5-ADJCHG: Process 1, Nbr 1.1.1.1 on GigabitEthernet0/1 from LOADING to FULL, Loading Done
```
Isso quer dizer: **os dois roteadores viraram vizinhos** e trocaram os mapas. 🎉

## Parte 4 · Servidor e PCs

**Servidor-SP** → Desktop → IP Configuration → **Static**:
- IP `192.168.1.10` · Máscara `255.255.255.0` · Gateway `192.168.1.1` · DNS `192.168.1.10`

Services → **HTTP** ligado (edite o `index.html`: `<h1>Sistema da Empresa - Matriz SP</h1>`).
Services → **DNS** ligado → `sistema.empresa.lab` → A Record → `192.168.1.10`.

**PC-SP, PC-RJ, PC-BH** → IP Configuration → **DHCP**.

## Parte 5 · Testes 📸

### 1. Vizinhos OSPF (em cada roteador)
```
show ip ospf neighbor
```
Cada roteador deve listar **2 vizinhos** em estado **FULL**.

### 2. Rotas aprendidas
No **R-RJ**:
```
show ip route ospf
```
Procure a linha da rede de BH:
```
O    192.168.3.0 [110/3] via 10.0.0.1, ..., GigabitEthernet0/1
```
- `O` = aprendida pelo OSPF
- `[110/3]` = 110 é a "confiança" do OSPF, 3 é o **custo** total
- `via 10.0.0.1` = o próximo salto é **São Paulo** (caminho principal)

Para ver os custos de cada link:
```
show ip ospf interface brief
```

### 3. Caminho normal
No **PC-RJ** → Command Prompt (troque pelo IP que o PC-BH recebeu):
```
tracert 192.168.3.11
```
O caminho passa por `10.0.0.1` (SP).

### 4. A grande demonstração: derrubar um link 💥
1. No **PC-BH**, comece um ping longo para o servidor:
   ```
   ping -n 50 192.168.1.10
   ```
2. **Enquanto o ping roda**, vá ao **R-SP** → CLI:
   ```
   configure terminal
   interface GigabitEthernet0/2
   shutdown
   ```
3. Volte ao PC-BH: alguns pings falham (`Request timed out`) e depois **voltam a responder sozinhos**. A rede se curou.

📸 **Print:** o ping com as falhas no meio e a volta.

### 5. Ver o desvio
No **PC-BH**:
```
tracert 192.168.1.10
```
Agora o caminho é: `192.168.3.1` → **`10.0.0.9`** (RJ) → `10.0.0.1` (SP) → servidor. O tráfego está usando o **link de backup**.

No **R-BH**:
```
show ip route ospf
```
A rede `192.168.1.0` agora aparece com custo **102**, via `10.0.0.9`.

### 6. Religar
No **R-SP**:
```
interface GigabitEthernet0/2
no shutdown
end
```
Repita o `tracert`: o caminho principal volta.

### 7. Testar a autenticação (opcional)
No **R-BH**:
```
configure terminal
interface GigabitEthernet0/1
ip ospf message-digest-key 1 md5 SenhaErrada
```
A vizinhança com o R-SP **cai**. Isso prova que um roteador sem a senha certa não entra na conversa. Para desfazer:
```
no ip ospf message-digest-key 1
ip ospf message-digest-key 1 md5 OspfLab26
end
```

### 8. Acesso ao sistema
No **PC-RJ** ou **PC-BH** → Web Browser → `http://sistema.empresa.lab` → a página da matriz abre.

**Prints sugeridos:** topologia, `show ip ospf neighbor`, `show ip route ospf` antes e depois da falha, `tracert` antes e depois, ping com a falha e a recuperação.

Salve como `wan-ospf.pkt` nesta pasta.

---

## Se algo der errado

| Sintoma | Verifique |
|---|---|
| Link vermelho entre roteadores | Cabo **cross-over**; `no shutdown` nas portas |
| Vizinhos não aparecem | Senha OSPF igual dos dois lados; `network` cobrindo o IP do link (`show ip protocols`) |
| Vizinho preso em EXSTART/EXCHANGE | Configurações diferentes de MTU (raro no Packet Tracer); salve e reabra o arquivo |
| PC não recebe IP | Pool DHCP do roteador local (`show ip dhcp pool`) |
| Ping falha só para uma filial | `show ip route` no roteador da origem: a rede de destino aparece? |
