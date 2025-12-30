from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from .auth import is_user_authorized
from .lldap import create_user, add_user_to_group, delete_user, find_username_by_email
from .config import ADMIN_GROUP_ID
from .utils import generate_random_password

# --- FUNCION QUE FALTABA (FIX) ---
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
        "🔹 Para borrar: `/baja email@usuario.com`\n",
        parse_mode=ParseMode.MARKDOWN
    )

# --- CREAR USUARIO (CON CONTRASEÑA) ---
async def create_user_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_user_authorized(update, context):
        return

    args = context.args
    if len(args) < 3:
        await update.effective_message.reply_text("⚠️ Uso: `/crear Nombre Apellido email@ejemplo.com`")
        return

    first_name, last_name, email = args[0], args[1], args[2]
    username = f"{first_name}.{last_name}".lower()
    display_name = f"{first_name} {last_name}"
    telegram_user = update.effective_user.first_name
    
    # 1. Generar contraseña aleatoria
    password = generate_random_password()

    await update.effective_message.reply_text(f"⏳ Creando usuario `{username}` con contraseña segura...")

    # 2. Crear en LLDAP pasando la contraseña
    success, output = create_user(username, email, password, display_name)
    if not success:
        await update.effective_message.reply_text(f"❌ Error creando usuario:\n{output}")
        return

    # 3. Añadir al grupo Jellyfin
    add_user_to_group(username, "jellyfin")

    # 4. Mensaje con CREDENCIALES (Privado)
    msg_private = (
        f"✅ **¡Cuenta Creada Exitosamente!**\n\n"
        f"🔐 **TUS CREDENCIALES:**\n"
        f"👤 Usuario: `{username}`\n"
        f"🔑 Contraseña: `{password}`\n\n"
        f"⚠️ _Guarda esta contraseña, no se puede recuperar, solo cambiar._\n\n"
        f"🔗 **Acceso directo:**\n"
        f"📺 [Jellyfin (Ver contenido)](https://jellyfin.pyam.org)\n"
        f"🎬 [Jellyseer (Pedir contenido)](https://jellyseer.pyam.org)\n"
    )
    # Hacemos que el usuario pueda copiar la contraseña haciendo click (Code style)
    await update.effective_message.reply_text(msg_private, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)

    # 5. Notificación al Grupo (SIN la contraseña por seguridad)
    if ADMIN_GROUP_ID:
        try:
            msg_group = (
                f"📢 **Nuevo usuario registrado**\n"
                f"El usuario de Telegram **{telegram_user}** ha creado la cuenta `{username}` asociada al email `{email}`."
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
                text=f"🗑️ **Usuario eliminado:** `{username_found}`", 
                parse_mode=ParseMode.MARKDOWN
            )
    else:
        await update.effective_message.reply_text(f"❌ Error al eliminar:\n{output}")