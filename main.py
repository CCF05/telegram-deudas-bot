import os
import json
from datetime import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

# 🧩 Variables de entorno
TOKEN = os.getenv("BOT_TOKEN")
AUTHORIZED_IDS = [int(i) for i in os.getenv("ADMIN_IDS", "7967718457").split(",")]

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

# 🧮 Agregar deuda
async def agregar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in AUTHORIZED_IDS:
        return await update.message.reply_text("🚫 No tienes permiso para usar este bot.")
    if len(context.args) < 2:
        return await update.message.reply_text("❗ Usa: /agregar <nombre> <cantidad> [descripción opcional]")

    nombre = context.args[0].capitalize()
    try:
        cantidad = float(context.args[1])
    except ValueError:
        return await update.message.reply_text("❗ La cantidad debe ser numérica.")

    descripcion = " ".join(context.args[2:]) if len(context.args) > 2 else ""
    fecha = datetime.now().strftime("%d/%m/%Y - %H:%M")

    if nombre not in registros:
        registros[nombre] = []
    registros[nombre].append({"tipo": "debe", "cantidad": cantidad, "descripcion": descripcion, "fecha": fecha})
    guardar()

    await update.message.reply_text(f"✅ {nombre} te debe {cantidad} ({descripcion})\n📅 {fecha}")

# 💵 Registrar pago
async def pago(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in AUTHORIZED_IDS:
        return await update.message.reply_text("🚫 No tienes permiso para usar este bot.")
    if len(context.args) < 2:
        return await update.message.reply_text("❗ Usa: /pago <nombre> <cantidad> [comentario opcional]")

    nombre = context.args[0].capitalize()
    try:
        cantidad = float(context.args[1])
    except ValueError:
        return await update.message.reply_text("❗ La cantidad debe ser numérica.")

    descripcion = " ".join(context.args[2:]) if len(context.args) > 2 else ""
    fecha = datetime.now().strftime("%d/%m/%Y - %H:%M")

    if nombre not in registros:
        registros[nombre] = []
    registros[nombre].append({"tipo": "pago", "cantidad": cantidad, "descripcion": descripcion, "fecha": fecha})
    guardar()

    await update.message.reply_text(f"💰 {nombre} pagó {cantidad} ({descripcion})\n📅 {fecha}")

# 📋 Ver por persona
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
    for mov in registros[nombre]:
        signo = "+" if mov["tipo"] == "debe" else "-"
        total += mov["cantidad"] if mov["tipo"] == "debe" else -mov["cantidad"]
        detalle += f"{signo}{mov['cantidad']} | {mov['descripcion']} | {mov['fecha']}\n"

    await update.message.reply_text(f"📒 {nombre}:\n{detalle}\n💲 Total actual: {total}")

# 📊 Total general
async def total(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in AUTHORIZED_IDS:
        return await update.message.reply_text("🚫 No tienes permiso.")

    resumen = ""
    total_general = 0
    for nombre, movs in registros.items():
        total = sum(m["cantidad"] if m["tipo"] == "debe" else -m["cantidad"] for m in movs)
        if total != 0:
            resumen += f"{nombre}: {total}\n"
            total_general += total

    await update.message.reply_text(f"💼 Total por persona:\n{resumen}\n💰 Total general: {total_general}")

# 🧾 Historial completo
async def historial(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in AUTHORIZED_IDS:
        return await update.message.reply_text("🚫 No tienes permiso.")
    if not registros:
        return await update.message.reply_text("🕳️ No hay movimientos aún.")

    texto = "📜 Historial completo:\n\n"
    for nombre, movs in registros.items():
        for m in movs:
            signo = "+" if m["tipo"] == "debe" else "-"
            texto += f"{nombre}: {signo}{m['cantidad']} | {m['descripcion']} | {m['fecha']}\n"

    await update.message.reply_text(texto)

# 🚀 Inicio
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id in AUTHORIZED_IDS:
        await update.message.reply_text("🤖 Bot activo y listo para registrar deudas y pagos.")
    else:
        await update.message.reply_text("🚫 No tienes permiso para usar este bot.")

# 🌐 Servidor HTTP dummy
class DummyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b"Bot is running!")
    
    def log_message(self, format, *args):
        pass

def run_server():
    port = int(os.getenv("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), DummyHandler)
    print(f"🌐 Servidor HTTP iniciado en puerto {port}")
    server.serve_forever()

# Inicia servidor HTTP en segundo plano
print("🚀 Iniciando servidor HTTP...")
server_thread = threading.Thread(target=run_server, daemon=True)
server_thread.start()

# Configurar bot
print("🤖 Configurando bot de Telegram...")
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("agregar", agregar))
app.add_handler(CommandHandler("pago", pago))
app.add_handler(CommandHandler("ver", ver))
app.add_handler(CommandHandler("total", total))
app.add_handler(CommandHandler("historial", historial))

print("✅ Bot corriendo 24/7 en Render...")
app.run_polling()
