# AFK (Bot)

Bot para Discord que gerencia usuários AFK com **timer público**, mostrando quem está “off” e há quanto tempo.

---

## 📌 Funcionalidades

- `/afk` → Marca o usuário como AFK e envia um timer público no canal de status.
- `/unafk` → Remove o status AFK e indica que o usuário voltou.
- Timer atualizado a cada 10 segundos no canal `⏳ | afk-status`.

---

## ⚙️ Configuração

1. Crie um arquivo `config.py` na raiz do projeto:

```python
import os

TOKEN = os.environ.get("TOKEN")         # Token do bot (variável de ambiente)
GUILD_ID = 1465477542919016625          # ID do seu servidor
AFK_CHANNEL_ID = 1466487369195720777   # ID do canal ⏳ | afk-status
