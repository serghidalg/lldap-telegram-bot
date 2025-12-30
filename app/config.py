import os
import logging
import sys

# Logging Setup
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Environment Variables
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
ADMIN_GROUP_ID = os.getenv("ADMIN_GROUP_ID")
LLDAP_URL = os.getenv("LLDAP_URL")
LLDAP_USER = os.getenv("LLDAP_USER")
LLDAP_PASSWORD = os.getenv("LLDAP_PASSWORD")
SERVICES_DESCRIPTION = (
    f"📺 [Jellyfin](https://jellyfin.pyam.org): ver series y pelis\n"
    f"🎬 [Jellyseerr](https://jellyseer.pyam.org): solicitar series y pelis\n"
    f"🎧 [Navidrome](https://musicx.pyam.org): escuchar música\n"
    f"🎶 [Deemix](https://getmusic.pyam.org): solicitar nueva música\n"
)

# Validation
if not TELEGRAM_TOKEN:
    logger.critical("TELEGRAM_TOKEN is missing!")
    sys.exit(1)

if not LLDAP_URL or not LLDAP_USER or not LLDAP_PASSWORD:
    logger.warning("LLDAP credentials or URL might be missing. Commands will fail.")