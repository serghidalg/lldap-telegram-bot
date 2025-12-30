from telegram.ext import ApplicationBuilder, CommandHandler
from .config import TELEGRAM_TOKEN, logger
from .handlers import start_handler, create_user_handler, delete_user_handler, get_id_handler

def main():
    logger.info("Starting bot...")
    
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    
    # Register Commands
    app.add_handler(CommandHandler('start', start_handler))
    app.add_handler(CommandHandler('crear', create_user_handler))
    app.add_handler(CommandHandler('baja', delete_user_handler))
    app.add_handler(CommandHandler('getid', get_id_handler))
    
    app.run_polling()

if __name__ == '__main__':
    main()