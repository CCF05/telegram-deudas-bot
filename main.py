import os
import json
from datetime import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from fastapi import FastAPI
import uvicorn
import threading

# ---------------- Configuración ----------------
TOKEN = os.getenv("BOT_TOKEN")  # Tu token del bot
PORT = int(os.getenv("PORT", 10000))  # Puerto para FastAPI
AUTHORIZED_IDS = [12345678]  # Reemplaza con los IDs que pueden usar el bot
DATA_FILE = "registros.json"

# ---------------- Cargar registros ----------------
if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r") as f:
        registros = json.load(f)
else:
    registros = {}

def guardar():
    with open(DATA_FILE, "w") as f:
        json.dump(registros, f, indent=4)

# ---------------- Comandos del Bot ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id in AUTHORIZED_IDS:
        await update.message.reply_text("🤖 Bot activo y listo.")
    else:
        await update.message.reply_text("🚫 No tienes permiso.")

async def agregar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in AUTHORIZED_IDS:
        return
    try:
        nombre = context.args[0]
        cantidad = float(context.args[1])
        descripcion = " ".join(context.args[2:])
        fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if nombre not in registros:
            registros[nombre] = []
        registros[nombre].append({"cantidad": cantidad, "descripcion": descripcion, "fecha": fecha})
        guardar()
        await update.message.reply_text(f"✅ Agregado a {nombre}: {cantidad} ({descripcion})")
    except Exception as e:
        await update.message.reply_text(f"⚠️ Error al agregar. Uso: /agregar Nombre Cantidad Descripción\n{e}")

async def pago(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in AUTHORIZED_IDS:
        return
    try:
        nombre = context.args[0]
        cantidad = float(context.args[1])
        descripcion = " ".join(context.args[2:])
        fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if nombre not in registros:
            registros[nombre] = []
        registros[nombre].append({"cantidad": -cantidad, "descripcion": descripcion, "fecha": fecha})
        guardar()
        await update.message.reply_text(f"💰 Pago registrado a {nombre}: {cantidad} ({descripcion})")
    except Exception as e:
        await update.message.reply_text(f"⚠️ Error al registrar pago. Uso: /pago Nombre Cantidad Descripción\n{e}")

async def ver(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in AUTHORIZED_IDS:
        return
    try:
        nombre = context.args[0]
        if nombre not in registros or not registros[nombre]:
            await update.message.reply_text(f"📭 No hay registros para {nombre}")
            return
        msg = f"📄 Registro de {nombre}:\n"
        for r in registros[nombre]:
            msg += f"{r['fecha']}: {r['cantidad']} ({r['descripcion']})\n"
        await update.message.reply_text(msg)
    except Exception as e:
        await update.message.reply_text(f"⚠️ Error. Uso: /ver Nombre\n{e}")

async def total(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in AUTHORIZED_IDS:
        return
    try:
        nombre = context.args[0]
        if nombre not in registros:
            await update.message.reply_text(f"📭 No hay registros para {nombre}")
            return
        total_valor = sum([r["cantidad"] for r in registros[nombre]])
        await update.message.reply_text(f"💲 Total de {nombre}: {total_valor}")
    except Exception as e:
        await update.message.reply_text(f"⚠️ Error. Uso: /total Nombre\n{e}")

async def eliminar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in AUTHORIZED_IDS:
        return
    try:
        nombre = context.args[0]
        if nombre in registros:
            registros.pop(nombre)
            guardar()
            await update.message.reply_text(f"🗑️ Se eliminaron todos los registros de {nombre}")
        else:
            await update.message.reply_text(f"📭 No hay registros para {nombre}")
    except Exception as e:
        await update.message.reply_text(f"⚠️ Error. Uso: /eliminar Nombre\n{e}")

# ---------------- FastAPI ----------------
app_api = FastAPI()

@app_api.get("/")
async def root():
    return {"status": "Bot is running!", "total_registros": len(registros)}

# ---------------- Ejecutar el Bot ----------------
def run_bot():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("agregar", agregar))
    app.add_handler(CommandHandler("pago", pago))
    app.add_handler(CommandHandler("ver", ver))
    app.add_handler(CommandHandler("total", total))
    app.add_handler(CommandHandler("eliminar", eliminar))
    app.run_polling()

# ---------------- Ejecutar FastAPI ----------------
def run_api():
    uvicorn.run(app_api, host="0.0.0.0", port=PORT)

# ---------------- Main ----------------
if __name__ == "__main__":
    # FastAPI en el hilo principal
    api_thread = threading.Thread(target=run_api)
    api_thread.start()

    # Bot en un hilo separado
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.start()

    # Mantener el main vivo
    api_thread.join()
    bot_thread.join()
