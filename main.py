```python
"""
railway_bot.py  ·  Ejecutar en Railway
Variables de entorno en Railway:
  DISCORD_TOKEN   → token del bot
  CANAL_ID        → ID del canal (número)
  SECRET_KEY      → clave compartida con la RPi (cualquier string)
"""
import os
import threading
from collections import deque
import discord
from flask import Flask, jsonify, request

# ─── Config ───────────────────────────────────────────────────────
DISCORD_TOKEN = os.environ["DISCORD_TOKEN"]
CANAL_ID      = int(os.environ["CANAL_ID"])
SECRET_KEY    = os.environ.get("SECRET_KEY", "carro_secreto_123")

# ─── Cola de comandos (thread-safe) ───────────────────────────────
cola: deque[str] = deque(maxlen=20)

# ─── Flask ────────────────────────────────────────────────────────
app = Flask(__name__)

@app.route("/cmd", methods=["GET"])
def get_cmd():
    if request.args.get("key") != SECRET_KEY:
        return jsonify({"error": "no autorizado"}), 403
    if cola:
        return jsonify({"cmd": cola.popleft()})
    return jsonify({"cmd": None})

@app.route("/health")
def health():
    return "ok", 200

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

# ─── Discord ──────────────────────────────────────────────────────
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

COMANDOS_VALIDOS = {
    "!adelante":  "F",
    "!atras":     "B",
    "!izquierda": "L",
    "!derecha":   "R",
    "!stop":      "S",
}

@client.event
async def on_ready():
    print(f"[Bot] Conectado como {client.user}")

@client.event
async def on_message(message: discord.Message):
    if message.author == client.user:
        return
    if message.channel.id != CANAL_ID:
        return

    partes  = message.content.strip().lower().split()
    cmd_str = partes[0] if partes else ""

    if cmd_str == "!ayuda":
        await message.channel.send(
            "**Comandos del carro:**\n"
            "`!adelante` `!atras` `!izquierda` `!derecha` `!stop`\n"
            "`!servo <0-180>` · `!distancia`"
        )
        return

    if cmd_str in COMANDOS_VALIDOS:
        cola.append(COMANDOS_VALIDOS[cmd_str])
        await message.add_reaction("✅")
        return

    if cmd_str == "!servo":
        if len(partes) < 2 or not partes[1].isdigit():
            await message.channel.send("❌ Uso: `!servo <0-180>`")
            return
        ang = max(0, min(180, int(partes[1])))
        cola.append(f"V{ang}")
        await message.add_reaction("🔄")
        return

    if cmd_str == "!distancia":
        cola.append("D")
        await message.add_reaction("📡")
        return

# ─── Arranque ─────────────────────────────────────────────────────
if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    client.run(DISCORD_TOKEN)
```

Igual que antes, sin ningún cambio.
