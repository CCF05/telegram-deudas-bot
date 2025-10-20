import os
import json
import asyncio
from datetime import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from fastapi import FastAPI
import uvicorn
import threading

# 🧩 Variables de entorno
TOKEN = os.getenv("BOT_TOKEN")

DATA_FILE = "registros.json"

# 📁 Cargar registros guardados
if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r") as f:
        registros = json.load(f)
else:
    registros = {}

def guardar():
    with open(DATA_FILE, "w") as f:
        json.dump(registros, f, indent=4)

# -------------------- Comandos del Bot --------------------

async def agregar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in AUTHORIZED_IDS:
        return await update.message.reply_text("🚫 No tienes permiso para usar este bot.")
    if len(context.args) < 2:
        return await update.message.reply_text("❗ Usa: /agregar <nombre> <cantidad> [descripción opcional] [fecha opcional DD/MM/YYYY]")

    nombre = context.args[0].capitalize()
    try:
        cantidad = float(context.args[1])
    except ValueError:
        return await update.message.reply_text("❗ La cantidad debe ser numérica.")

    fecha_manual = None
    if len(context.args) > 2:
        posible_fecha = context.args[-1]
        try:
            fecha_manual = datetime.strptime(posible_fecha, "%d/%m/%Y").strftime("%d/%m/%Y")
            descripcion = " ".join(context.args[2:-1])
        except ValueError:
            descripcion = " ".join(context.args[2:])
    else:
        descripcion = ""

    fecha = fecha_manual if fecha_manual else datetime.now().strftime("%d/%m/%Y - %H:%M")

    if nombre not in registros:
        registros[nombre] = []
    registros[nombre].append({"tipo": "debe", "cantidad": cantidad, "descripcion": descripcion, "fecha": fecha})
    guardar()

    await update.message.reply_text(f"✅ {nombre} te debe {cantidad} ({descripcion})\n📅 {fecha}")

async def pago(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in AUTHORIZED_IDS:
        return await update.message.reply_text("🚫 No tienes permiso para usar este bot.")
    if len(context.args) < 2:
        return await update.message.reply_text("❗ Usa: /pago <nombre> <cantidad> [comentario opcional] [fecha opcional DD/MM/YYYY]")

    nombre = context.args[0].capitalize()
    try:
        cantidad = float(context.args[1])
    except ValueError:
        return await update.message.reply_text("❗ La cantidad debe ser numérica.")

    fecha_manual = None
    if len(context.args) > 2:
        posible_fecha = context.args[-1]
        try:
            fecha_manual = datetime.strptime(posible_fecha, "%d/%m/%Y").strftime("%d/%m/%Y")
            descripcion = " ".join(context.args[2:-1])
        except ValueError:
            descripcion = " ".join(context.args[2:])
    else:
        descripcion = ""

    fecha = fecha_manual if fecha_manual else datetime.now().strftime("%d/%m/%Y - %H:%M")

    if nombre not in registros:
        registros[nombre] = []
    registros[nombre].append({"tipo": "pago", "cantidad": cantidad, "descripcion": descripcion, "fecha": fecha})
    guardar()

    await update.message.reply_text(f"💰 {nombre} pagó {cantidad} ({descripcion})\n📅 {fecha}")

async def ver(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in AUTHORIZED_IDS:
        return await update.message.reply_text("🚫 No tienes permiso.")
    if len(context.args) < 1:
        return await update.message.reply_text("❗ Usa: /ver <nombre>")

    nombre = context.args[0].capitalize()
    if nombre not in registros:
        return await update.message.reply_text(f"❌ No hay registros de {nombre}.")

    total = 0
    detalle = ""
    for idx, mov in enumerate(registros[nombre], start=1):
        signo = "+" if mov["tipo"] == "debe" else "-"
        total += mov["cantidad"] if mov["tipo"] == "debe" else -mov["cantidad"]
        detalle += f"{idx}. {signo}{mov['cantidad']} | {mov['descripcion']} | {mov['fecha']}\n"

    await update.message.reply_text(f"📒 {nombre}:\n{detalle}\n💲 Total actual: {total}")

async def total(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in AUTHORIZED_IDS:
        return await update.message.reply_text("🚫 No tienes permiso.")

    resumen = ""
    total_general = 0
    for nombre, movs in registros.items():
        total_persona = sum(m["cantidad"] if m["tipo"] == "debe" else -m["cantidad"] for m in movs)
        if total_persona != 0:
            resumen += f"{nombre}: {total_persona}\n"
            total_general += total_persona

    if not resumen:
        return await update.message.reply_text("📭 No hay deudas pendientes.")

    await update.message.reply_text(f"💼 Total por persona:\n{resumen}\n💰 Total general: {total_general}")

async def historial(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in AUTHORIZED_IDS:
        return await update.message.reply_text("🚫 No tienes permiso.")
    if not registros:
        return await update.message.reply_text("🕳️ No hay movimientos aún.")

    texto = "📜 Historial completo:\n\n"
    for nombre, movs in registros.items():
        for idx, m in enumerate(movs, start=1):
            signo = "+" if m["tipo"] == "debe" else "-"
            texto += f"{idx}. {nombre}: {signo}{m['cantidad']} | {m['descripcion']} | {m['fecha']}\n"

    await update.message.reply_text(texto)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id in AUTHORIZED_IDS:
        await update.message.reply_text("🤖 Bot activo y listo para registrar deudas y pagos.")
    else:
        await update.message.reply_text("🚫 No tienes permiso para usar este bot.")

async def eliminar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in AUTHORIZED_IDS:
        return await update.message.reply_text("🚫 No tienes permiso para usar este bot.")
    if len(context.args) < 1:
        return await update.message.reply_text("❗ Usa: /eliminar <nombre> [índice]")

    nombre = context.args[0].capitalize()
    if nombre not in registros:
        return await update.message.reply_text(f"❌ No hay registros de {nombre}.")

    # Solo nombre -> eliminar todo
    if len(context.args) == 1:
        del registros[nombre]
        guardar()
        return await update.message.reply_text(f"🗑️ Se eliminaron todos los registros de {nombre}.")

    # Nombre + índice -> eliminar movimiento específico
    try:
        idx = int(context.args[1])
    except ValueError:
        return await update.message.reply_text("❗ El índice debe ser un número entero (ej: 1).")

    movs = registros[nombre]
    if idx < 1 or idx > len(movs):
        return await update.message.reply_text(f"❗ Índice inválido. {nombre} tiene {len(movs)} movimientos.")

    eliminado = movs.pop(idx - 1)
    if not movs:
        del registros[nombre]
    guardar()

    tipo = "debe" if eliminado["tipo"] == "debe" else "pagó"
    return await update.message.reply_text(f"🗑️ Eliminado: {nombre} {tipo} {eliminado['cantidad']} | {eliminado['descripcion']} | {eliminado['fecha']}")

# -------------------- FastAPI para mantener activo --------------------
app_api = FastAPI()

@app_api.get("/")
async def root():
    return {"status": "Bot is running!", "bot": "telegram-deudas-bot"}

@app_api.get("/health")
async def health():
    return {"status": "healthy", "registros": len(registros)}

# -------------------- Función para iniciar bot --------------------
async def run_bot():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("agregar", agregar))
    app.add_handler(CommandHandler("pago", pago))
    app.add_handler(CommandHandler("ver", ver))
    app.add_handler(CommandHandler("total", total))
    app.add_handler(CommandHandler("historial", historial))
    app.add_handler(CommandHandler("eliminar", eliminar))
    
    print("🚀 Iniciando bot de Telegram...")
    await app.initialize()
    await app.start()
    print("✅ Bot de Telegram corriendo...")
    await app.updater.start_polling()
    
    # Mantener el bot vivo
    await asyncio.Event().wait()

# -------------------- Ejecutar FastAPI + Bot --------------------
def main():
    print("🔧 Configurando servicios...")
    
    # Ejecutar bot en hilo separado con asyncio
    def start_bot():
        asyncio.run(run_bot())
    
    bot_thread = threading.Thread(target=start_bot, daemon=True)
    bot_thread.start()
    
    print("🌐 Iniciando servidor web...")
    # Ejecutar servidor FastAPI en puerto de Render
    port = int(os.getenv("PORT", 10000))
    uvicorn.run(app_api, host="0.0.0.0", port=port, log_level="info")

if __name__ == "__main__":
    main()
