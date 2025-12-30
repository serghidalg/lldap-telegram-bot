from telegram import Update
from telegram.ext import ContextTypes
from .auth import is_user_authorized
from .lldap import create_user, add_user_to_group, delete_user

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_user_authorized(update, context):
        await update.message.reply_text("⛔ Acceso denegado.")
        return

    await update.message.reply_text(
        "👋 **Panel de Control LLDAP**\n\n"
        "Comandos:\n"
        "🔹 `/crear Nombre Apellido Email`\n"
        "🔹 `/baja usuario`\n"
        "🔹 `/getid` (Ver ID de grupo)",
        parse_mode='Markdown'
    )

async def get_id_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    await update.message.reply_text(f"🆔 ID: `{chat_id}`", parse_mode='Markdown')

async def create_user_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_user_authorized(update, context):
        return

    args = context.args
    if len(args) < 3:
        await update.message.reply_text("⚠️ Uso: `/crear Nombre Apellido email@test.com`")
        return

    first_name, last_name, email = args[0], args[1], args[2]
    username = f"{first_name}.{last_name}".lower()
    display_name = f"{first_name} {last_name}"

    await update.message.reply_text(f"⏳ Procesando usuario `{username}`...")

    # 1. Create in LLDAP
    success, output = create_user(username, email, display_name)
    if not success:
        await update.message.reply_text(f"❌ Error al crear usuario:\n{output}")
        return

    # 2. Add to Jellyfin Group
    success_grp, output_grp = add_user_to_group(username, "jellyfin")
    if not success_grp:
        await update.message.reply_text(f"⚠️ Usuario creado, pero error al añadir al grupo:\n{output_grp}")

    # 3. Final Message
    msg = (
        f"✅ **Usuario Creado**\n\n"
        f"👤 User: `{username}`\n"
        f"📧 Email: `{email}`\n\n"
        f"🔗 **Enlaces:**\n"
        f"1. [Crear Contraseña](https://users.serghidalg.com/reset-password/step1)\n"
        f"2. [Solicitar Contenido](https://jellyseer.serghidalg.com)\n"
        f"3. [Ver Jellyfin](https://jellyfin.serghidalg.com)\n"
    )
    await update.message.reply_text(msg, parse_mode='Markdown', disable_web_page_preview=True)

async def delete_user_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_user_authorized(update, context):
        return

    if not context.args:
        await update.message.reply_text("⚠️ Uso: `/baja username`")
        return

    username = context.args[0]
    success, output = delete_user(username)

    if success:
        await update.message.reply_text(f"✅ Usuario `{username}` eliminado.")
    else:
        await update.message.reply_text(f"❌ Error al eliminar:\n{output}")