from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from .auth import is_user_authorized
from .lldap import create_user, add_user_to_group, delete_user, find_username_by_email, update_user_password
from .config import ADMIN_GROUP_ID
from .utils import generate_random_password

# --- UTILIDAD: OBTENER ID ---
async def get_id_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    await update.effective_message.reply_text(f"🆔 ID: `{chat_id}`", parse_mode='Markdown')

# --- BIENVENIDA AL GRUPO ---
async def new_member_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for member in update.effective_message.new_chat_members:
        if member.id == context.bot.id:
            continue
            
        keyboard = [[InlineKeyboardButton("🚀 Crear mi cuenta", url=f"https://t.me/{context.bot.username}?start=crear")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.effective_message.reply_text(
            f"👋 ¡Bienvenido {member.first_name}!\n\n"
            "Para acceder a los servicios, necesitas crear una cuenta.\n"
            "Pulsa el botón de abajo para que el bot te genere tus credenciales.",
            reply_markup=reply_markup
        )

# --- COMANDO START ---
async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_user_authorized(update, context):
        await update.effective_message.reply_text("⛔ Debes ser miembro del grupo de administración.")
        return

    await update.effective_message.reply_text(
        "👋 **Gestión de Usuarios LLDAP**\n\n"
        "🔹 Para crear: `/crear Nombre Apellido email`\n"
        "🔹 Para borrar: `/baja email@usuario.com`\n"
        "🔹 Ver ID Grupo: `/getid`\n"
        "_(El borrado se hace por email)_",
        parse_mode=ParseMode.MARKDOWN
    )

# --- CREAR USUARIO (CON PASSWORD, NOMBRE, APELLIDO Y TELEGRAM ID) ---
async def create_user_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_user_authorized(update, context):
        return

    args = context.args
    if len(args) < 3:
        await update.effective_message.reply_text("⚠️ Uso: `/crear Nombre Apellido email@ejemplo.com`")
        return

    # Recogemos los datos limpios
    first_name = args[0]
    last_name = args[1]
    email = args[2]
    
    # Username: nombre.apellido
    username = f"{first_name}.{last_name}".lower()
    
    # ID de Telegram para el atributo custom
    telegram_id_value = str(update.effective_user.id)
    telegram_user_name = update.effective_user.first_name
    
    # Generar password
    password = generate_random_password()

    await update.effective_message.reply_text(f"⏳ Creando usuario `{username}`...")

    # Llamamos a create_user pasando first_name y last_name por separado
    success, output = create_user(
        username=username, 
        email=email, 
        password=password, 
        first_name=first_name, 
        last_name=last_name, 
        telegram_id=telegram_user_name
    )
    
    if not success:
        await update.effective_message.reply_text(f"❌ Error creando usuario:\n{output}")
        return

    # Añadir al grupo Jellyfin
    add_user_to_group(username, "jellyfin")

    # Mensaje privado con credenciales
    msg_private = (
        f"✅ **¡Cuenta Creada Exitosamente!**\n\n"
        f"🔐 **TUS CREDENCIALES:**\n"
        f"👤 Usuario: `{username}`\n"
        f"🔑 Contraseña: `{password}`\n\n"
        f"⚠️ _Por favor, cámbiala [aquí](https://users.pyam.org) o guárdala en un lugar seguro._"
        f"🔗 **Acceso directo:**\n"
        f"📺 [Jellyfin](https://jellyfin.serghidalg.com)\n"
        f"🎬 [Jellyseer](https://jellyseer.serghidalg.com)\n"
    )
    await update.effective_message.reply_text(msg_private, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)

    # Notificación al Grupo
    if ADMIN_GROUP_ID:
        try:
            msg_group = (
                f"📢 **Nuevo usuario registrado**\n"
                f"El usuario de Telegram **{telegram_user_name}** ha creado la cuenta `{username}`."
            )
            await context.bot.send_message(chat_id=ADMIN_GROUP_ID, text=msg_group, parse_mode=ParseMode.MARKDOWN)
        except Exception:
            pass

# --- BAJA USUARIO (POR EMAIL) ---
async def delete_user_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_user_authorized(update, context):
        return

    args = context.args
    if len(args) < 1:
        await update.effective_message.reply_text("⚠️ Uso: `/baja email@ejemplo.com`")
        return

    input_email = args[0]
    
    await update.effective_message.reply_text(f"🔎 Buscando usuario con email `{input_email}`...")

    # 1. Buscar el username asociado a ese email
    username_found = find_username_by_email(input_email)
    
    if not username_found:
        await update.effective_message.reply_text(f"❌ No he encontrado ningún usuario con el email `{input_email}` en LLDAP.")
        return

    # 2. Proceder al borrado usando el username encontrado
    success, output = delete_user(username_found)

    if success:
        await update.effective_message.reply_text(f"✅ El usuario `{username_found}` (Email: {input_email}) ha sido eliminado.")
        
        # Log al grupo
        if ADMIN_GROUP_ID:
            await context.bot.send_message(
                chat_id=ADMIN_GROUP_ID, 
                text=f"🗑️ **Usuario eliminado:** `{username_found}` (solicitado vía email)", 
                parse_mode=ParseMode.MARKDOWN
            )
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

    input_email = args[0]
    
    await update.effective_message.reply_text(f"🔎 Buscando usuario con email `{input_email}`...")

    # 1. Buscar el username asociado al email
    username_found = find_username_by_email(input_email)
    
    if not username_found:
        await update.effective_message.reply_text(f"❌ No he encontrado ningún usuario con el email `{input_email}`.")
        return

    # 2. Generar nueva contraseña
    new_password = generate_random_password()
    
    # 3. Actualizar en LLDAP
    success, output = update_user_password(username_found, new_password)

    if success:
        # Mensaje PRIVADO con la nueva contraseña
        msg_private = (
            f"✅ **Contraseña Restaurada**\n\n"
            f"Se ha generado una nueva clave para el usuario `{username_found}`:\n\n"
            f"🔑 Nueva Contraseña: `{new_password}`\n\n"
            f"⚠️ _Por favor, cámbiala [aquí](https://users.pyam.org) o guárdala en un lugar seguro._"
        )
        await update.effective_message.reply_text(msg_private, parse_mode=ParseMode.MARKDOWN)
    else:
        await update.effective_message.reply_text(f"❌ Error al actualizar la contraseña:\n{output}")