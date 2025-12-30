from telegram import Update
from telegram.ext import ContextTypes
from telegram.error import BadRequest
from .config import ADMIN_GROUP_ID, logger

async def is_user_authorized(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """
    Verifies if the user is a member of the Admin Group.
    """
    user_id = update.effective_user.id
    
    # Bypass if no group is configured (Dev mode)
    if not ADMIN_GROUP_ID:
        return True

    try:
        member = await context.bot.get_chat_member(chat_id=ADMIN_GROUP_ID, user_id=user_id)
        if member.status in ['creator', 'administrator', 'member']:
            return True
        else:
            logger.warning(f"Unauthorized access attempt by user_id: {user_id}")
            return False

    except BadRequest as e:
        logger.error(f"Cannot verify group membership. Is the bot in the group? Error: {e}")
        await update.message.reply_text("⚠️ Error interno: No puedo verificar los permisos del grupo.")
        return False
    except Exception as e:
        logger.error(f"Unexpected auth error: {e}")
        return False