from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from .auth import is_user_authorized
from .lldap import create_user, add_user_to_group, delete_user, find_username_by_email, update_user_password
from .config import ADMIN_GROUP_ID, SERVICES_LIST, SERVICES_DESCRIPTION
from .utils import generate_random_password


#### VARIABLE DEFINITION
# --- UTILIDAD: OBTENER ID ---
async def get_id_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    await update.effective_message.reply_text(f"🆔 ID: `{chat_id}`", parse_mode='Markdown')

# --- UTILIDAD: SERVICES ---
async def services_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    await update.effective_message.reply_text(SERVICES_LIST, parse_mode='Markdown')

# --- UTILIDAD: DESCRIPTION ---
async def info_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    await update.effective_message.reply_text(SERVICES_DESCRIPTION, parse_mode='Markdown')


# --- BIENVENIDA AL GRUPO ---
async def new_member_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for member in update.effective_message.new_chat_members:
        if member.id == context.bot.id:
            continue
            
        keyboard = [[InlineKeyboardButton("🚀 Crear mi cuenta", url=f"https://t.me/{context.bot.username}?start=crear")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.effective_message.reply_text(
            f"👋 ¡Bienvenid@ {member.first_name}!\n\n"
            "Para acceder a los servicios, necesitas crear una cuenta.\n"
            "Pulsa el botón de abajo para que el bot genere tus credenciales.",
            reply_markup=reply_markup
        )

# --- COMANDO START ---
async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_user_authorized(update, context):
        await update.effective_message.reply_text("⛔ Debes ser miembro del grupo de administración.")
        return

    await update.effective_message.reply_text(
        "👋 **Gestión de Usuarios LLDAP**\n\n"
        " - Para crear: `/crear Nombre Apellido email`\n"
        " - Para borrar: `/baja email@usuario.com`\n"
        " - Restaurar contraseña: `/reset email@usuario.com`\n",
        parse_mode=ParseMode.MARKDOWN
    )

# --- CREAR USUARIO ---
async def create_user_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_user_authorized(update, context):
        return

    args = context.args
    if len(args) < 3:
        await update.effective_message.reply_text("⚠️ Uso: `/crear Nombre Apellido email@ejemplo.com`")
        return

    # Limpiamos los datos: strip() quita espacios accidentales
    first_name = args[0].strip()
    last_name = args[1].strip()
    email = args[2].strip().lower() # Guardamos siempre en minúsculas
    
    username = f"{first_name}.{last_name}".lower()
    
    # ID de Telegram (Guardamos el ID numérico que es más seguro y único que el nombre)
    telegram_id_value = str(update.effective_user.id)
    telegram_user_name = update.effective_user.first_name
    
    password = generate_random_password()

    await update.effective_message.reply_text(f"⏳ Creando usuario `{username}`...")

    success, output = create_user(
        username=username, 
        email=email, 
        password=password, 
        first_name=first_name, 
        last_name=last_name,
        telegram_username=telegram_user_name,
        telegram_id=telegram_id_value # Usamos el ID numérico
    )
    
    if not success:
        await update.effective_message.reply_text(f"❌ Error creando usuario:\n{output}")
        return

    add_user_to_group(username, "jellyfin")

    msg_private = (
        f"✅ **¡Cuenta Creada Exitosamente!**\n\n"
        f"🔐 **TUS CREDENCIALES:**\n"
        f"👤 Usuario: `{username}`\n"
        f"🔑 Contraseña: `{password}`\n\n"
        f"⚠️ _Por favor, cámbiala_ [aquí](https://users.pyam.org) _o guárdala en un lugar seguro._\n\n"
        f"🔗 **Acceso directo:**\n"
        f"{SERVICES_LIST}"
    )
    await update.effective_message.reply_text(msg_private, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)

    if ADMIN_GROUP_ID:
        try:
            msg_group = (
                f"📢 **Nuevo usuario registrado**\n"
                f"El usuario de Telegram **{telegram_user_name}** acaba de crear una cuenta."
            )
            await context.bot.send_message(chat_id=ADMIN_GROUP_ID, text=msg_group, parse_mode=ParseMode.MARKDOWN)
        except Exception:
            pass

# --- BAJA USUARIO ---
async def delete_user_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_user_authorized(update, context):
        return

    args = context.args
    if len(args) < 1:
        await update.effective_message.reply_text("⚠️ Uso: `/baja email@ejemplo.com`")
        return

    input_email = args[0].strip().lower()
    
    await update.effective_message.reply_text(f"🔎 Buscando usuario con email `{input_email}`...")

    username_found = find_username_by_email(input_email)
    
    if not username_found:
        await update.effective_message.reply_text(f"❌ No he encontrado ningún usuario con el email `{input_email}`.")
        return

    success, output = delete_user(username_found)

    if success:
        await update.effective_message.reply_text(f"✅ Usuario `{username_found}` eliminado.")
    else:
        await update.effective_message.reply_text(f"❌ Error al eliminar:\n{output}")

# --- RESTAURAR CONTRASEÑA ---
async def reset_password_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_user_authorized(update, context):
        return

    args = context.args
    if len(args) < 1:
        await update.effective_message.reply_text("⚠️ Uso: `/reset email@ejemplo.com`")
        return

    input_email = args[0].strip().lower()
    
    await update.effective_message.reply_text(f"🔎 Buscando usuario con email `{input_email}`...")

    username_found = find_username_by_email(input_email)
    
    if not username_found:
        await update.effective_message.reply_text(f"❌ No he encontrado ningún usuario con el email `{input_email}`.")
        return

    new_password = generate_random_password()
    success, output = update_user_password(username_found, new_password)

    if success:
        msg_private = (
            f"✅ **Contraseña Restaurada**\n\n"
            f"Se ha generado una nueva clave para el usuario `{username_found}`:\n\n"
            f"🔑 Nueva Contraseña: `{new_password}`\n\n"
            f"⚠️ _Por favor, cámbiala_ [aquí](https://users.pyam.org) _lo antes posible._"
        )
        await update.effective_message.reply_text(msg_private, parse_mode=ParseMode.MARKDOWN)
    else:
        await update.effective_message.reply_text(f"❌ Error al actualizar la contraseña:\n{output}")