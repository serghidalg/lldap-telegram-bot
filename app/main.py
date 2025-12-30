from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
from .config import TELEGRAM_TOKEN, logger
from .handlers import start_handler, create_user_handler, delete_user_handler, get_id_handler, new_member_handler, reset_password_handler

def main():
    logger.info("Starting bot (Stateless Mode)...")
    
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    
    # Comandos
    app.add_handler(CommandHandler('start', start_handler))
    app.add_handler(CommandHandler('crear', create_user_handler))
    app.add_handler(CommandHandler('reset', reset_password_handler))
    app.add_handler(CommandHandler('baja', delete_user_handler))
    app.add_handler(CommandHandler('getid', get_id_handler))
    
    # Detector de bienvenida (Nuevos miembros en el grupo)
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, new_member_handler))
    
    app.run_polling()

if __name__ == '__main__':
    main()