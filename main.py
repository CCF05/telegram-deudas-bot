import json
import os
from datetime import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# 🔐 Lista de IDs autorizados (agrega aquí tus IDs)
AUTORIZADOS = [7967718457]  # <--- reemplaza con tu ID real

# 📁 Archivo donde se guardarán las deudas
ARCHIVO = "deudas.json"

# 🧮 Cargar datos guardados o crear archivo vacío
def cargar_datos():
    if os.path.exists(ARCHIVO):
        with open(ARCHIVO, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def guardar_datos(datos):
    with open(ARCHIVO, "w", encoding="utf-8") as f:
        json.dump(datos, f, indent=4, ensure_ascii=False)

# 📋 /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in AUTORIZADOS:
        await update.message.reply_text("🚫 No estás autorizado para usar este bot.")
        return

    await update.message.reply_text(
        "👋 ¡Hola! Soy tu bot de registro de deudas.\n\n"
        "Puedes escribir frases como:\n"
        "- Magaly me debe 1000 de efectivo\n"
        "- Magaly me depositó 500\n\n"
        "Comandos disponibles:\n"
        "💰 /ver → muestra los totales por persona\n"
        "📋 /detalle → muestra todos los movimientos guardados"
    )

# 🧾 Registrar mensajes
async def registrar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if int(user_id) not in AUTORIZADOS:
        await update.message.reply_text("🚫 No estás autorizado para usar este bot.")
        return

    texto = update.message.text.lower()
    datos = cargar_datos()

    if user_id not in datos:
        datos[user_id] = {}

    personas = datos[user_id]

    nombre = None
    cantidad = 0
    motivo = ""

    palabras = texto.split()
    for i, palabra in enumerate(palabras):
        if palabra == "me" and i + 1 < len(palabras) and palabras[i + 1] in ["debe", "depositó", "deposito"]:
            nombre = palabras[i - 1].capitalize()
            try:
                cantidad = float(palabras[i + 2])
            except:
                await update.message.reply_text("❌ No pude leer la cantidad.")
                return

            if "debe" in palabras[i + 1]:
                signo = 1
            else:
                signo = -1

            motivo = " ".join(palabras[i + 3:])
            fecha = datetime.now().strftime("%Y-%m-%d %H:%M")

            if nombre not in personas:
                personas[nombre] = {"total": 0, "movimientos": []}

            personas[nombre]["total"] += signo * cantidad
            personas[nombre]["movimientos"].append({
                "fecha": fecha,
                "tipo": "debe" if signo == 1 else "depositó",
                "cantidad": cantidad,
                "motivo": motivo
            })

            guardar_datos(datos)
            total_actual = personas[nombre]["total"]
            await update.message.reply_text(f"✅ Registro guardado.\n{nombre} ahora tiene un total de {total_actual}.")
            return

    await update.message.reply_text("⚠️ No entendí el formato. Usa frases como:\n'Magaly me debe 500 de tacos'.")

# 💰 /ver — totales por persona
async def ver(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if int(user_id) not in AUTORIZADOS:
        await update.message.reply_text("🚫 No estás autorizado para usar este bot.")
        return

    datos = cargar_datos()
    if user_id not in datos or not datos[user_id]:
        await update.message.reply_text("📭 No tienes registros todavía.")
        return

    respuesta = "💰 Totales de tus registros:\n"
    for nombre, info in datos[user_id].items():
        respuesta += f"{nombre}: {info['total']}\n"

    await update.message.reply_text(respuesta)

# 📋 /detalle — todos los movimientos
async def detalle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if int(user_id) not in AUTORIZADOS:
        await update.message.reply_text("🚫 No estás autorizado para usar este bot.")
        return

    datos = cargar_datos()
    if user_id not in datos or not datos[user_id]:
        await update.message.reply_text("📭 No tienes movimientos todavía.")
        return

    respuesta = ""
    for nombre, info in datos[user_id].items():
        respuesta += f"📋 Detalle de {nombre}:\n"
        for mov in info["movimientos"]:
            signo = "+" if mov["tipo"] == "debe" else "-"
            respuesta += f"{signo}{mov['cantidad']} {mov['motivo']} ({mov['fecha']})\n"
        respuesta += f"Total: {info['total']}\n\n"

    await update.message.reply_text(respuesta)

# 🚀 Ejecutar el bot
if __name__ == "__main__":
    TOKEN = os.getenv("BOT_TOKEN")  # <-- Render lo tomará desde la variable de entorno
    if not TOKEN:
        print("❌ Error: No se encontró la variable BOT_TOKEN.")
        exit()

    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("ver", ver))
    app.add_handler(CommandHandler("detalle", detalle))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, registrar))

    print("✅ Bot encendido y escuchando mensajes...")

    app.run_polling()
