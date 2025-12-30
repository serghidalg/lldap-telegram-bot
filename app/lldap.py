import subprocess
import logging
from .config import LLDAP_URL, LLDAP_USER, LLDAP_PASSWORD

logger = logging.getLogger(__name__)

def _run_shell_command(command: str) -> tuple[bool, str]:
    """Internal helper to execute shell commands with LLDAP login context."""
    try:
        # Login creates a temporary token session
        login_cmd = f"lldap-cli -H {LLDAP_URL} -D {LLDAP_USER} -w \"{LLDAP_PASSWORD}\" login"
        
        # Execute login AND the requested command
        full_cmd = f"eval $({login_cmd}) && {command}"
        
        result = subprocess.run(
            full_cmd, 
            shell=True, 
            check=True, 
            capture_output=True, 
            text=True, 
            executable='/bin/bash'
        )
        return True, result.stdout.strip()
    except subprocess.CalledProcessError as e:
        return False, e.stderr

def create_user(username: str, email: str, password: str, display_name: str, first_name: str, last_name: str) -> tuple[bool, str]:
    # NOTE: lldap-cli syntax is usually: user add <username> <email> [password]
    # We wrap password in quotes to handle special characters
    cmd = f"lldap-cli user add {username} {email} '{password}' -d \"{display_name}\" -f {first_name} -l {last_name}"
    return _run_shell_command(cmd)

def add_user_to_group(username: str, group_name: str) -> tuple[bool, str]:
    cmd = f"lldap-cli user group add {username} {group_name}"
    return _run_shell_command(cmd)

def delete_user(username: str) -> tuple[bool, str]:
    cmd = f"lldap-cli user del {username}"
    return _run_shell_command(cmd)

def find_username_by_email(email: str) -> str | None:
    """
    Parses lldap-cli user list to find the username associated with an email.
    Returns the username if found, or None.
    """
    # Get list of all users
    success, output = _run_shell_command("lldap-cli user list")
    
    if not success:
        logger.error(f"Error listing users: {output}")
        return None

    # lldap-cli output is typically human readable lines.
    # We will search line by line.
    search_email = email.lower().strip()
    
    for line in output.splitlines():
        # Check if email exists in this line
        if search_email in line.lower():
            # Usually the first word in the line is the username (User ID)
            # Example output: "admin admin@example.com 'Admin User'"
            parts = line.split()
            if len(parts) > 0:
                return parts[0] # Return the username
            
    return None