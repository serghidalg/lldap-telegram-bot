import subprocess
import logging
from .config import LLDAP_URL, LLDAP_USER, LLDAP_PASSWORD

logger = logging.getLogger(__name__)

def _run_shell_command(command: str) -> tuple[bool, str]:
    try:
        login_cmd = f"lldap-cli -H {LLDAP_URL} -D {LLDAP_USER} -w \"{LLDAP_PASSWORD}\" login"
        full_cmd = f"eval $({login_cmd}) && {command}"
        result = subprocess.run(full_cmd, shell=True, check=True, capture_output=True, text=True, executable='/bin/bash')
        return True, result.stdout.strip()
    except subprocess.CalledProcessError as e:
        return False, e.stderr

def create_user(username: str, email: str, password: str, first_name: str, last_name: str, telegram_id: str = None, telegram_username: str = None) -> tuple[bool, str]:
    display_name = f"{first_name} {last_name}"
    cmd_add = f"lldap-cli user add {username} {email} -p '{password}' -f \"{first_name}\" -l \"{last_name}\" -d \"{username}\""
    
    success, output = _run_shell_command(cmd_add)
    if not success: return False, output

    if telegram_username:
        cmd_telegram_username = f"lldap-cli user update set {username} telegram '{telegram_username}'"
        _run_shell_command(cmd_telegram_username)
            
    if telegram_id:
        cmd_telegram_id = f"lldap-cli user update set {username} telegram-id '{telegram_id}'"
        _run_shell_command(cmd_telegram_id) 
            
    return True, output

def add_user_to_group(username: str, group_name: str) -> tuple[bool, str]:
    cmd = f"lldap-cli user group add {username} {group_name}"
    return _run_shell_command(cmd)

def delete_user(username: str) -> tuple[bool, str]:
    cmd = f"lldap-cli user del {username}"
    return _run_shell_command(cmd)

def update_user_password(username: str, new_password: str) -> tuple[bool, str]:
    cmd = f"lldap-cli user update set {username} password '{new_password}'"
    return _run_shell_command(cmd)

def find_username_by_email(email: str) -> str | None:
    cmd = (
        f"lldap-cli user info {email} | "
        "awk 'NR>2 {print $1}'"
    )

    success, output = _run_shell_command(cmd)
    if not success:
        return None

    return output.strip() or None
