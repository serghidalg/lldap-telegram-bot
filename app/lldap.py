import subprocess
from .config import LLDAP_URL, LLDAP_USER, LLDAP_PASSWORD

def _run_shell_command(command: str) -> tuple[bool, str]:
    """Internal helper to execute shell commands with LLDAP login context."""
    try:
        # Login creates a temporary token session
        login_cmd = f"lldap-cli -H {LLDAP_URL} -D {LLDAP_USER} -w \"{LLDAP_PASSWORD}\" login"
        
        # Execute login AND the requested command in the same shell instance
        full_cmd = f"eval $({login_cmd}) && {command}"
        
        result = subprocess.run(
            full_cmd, 
            shell=True, 
            check=True, 
            capture_output=True, 
            text=True, 
            executable='/bin/bash'
        )
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        return False, e.stderr

def create_user(username: str, email: str, display_name: str) -> tuple[bool, str]:
    cmd = f"lldap-cli user add {username} {email} -d \"{display_name}\""
    return _run_shell_command(cmd)

def add_user_to_group(username: str, group_name: str) -> tuple[bool, str]:
    cmd = f"lldap-cli user group add {username} {group_name}"
    return _run_shell_command(cmd)

def delete_user(username: str) -> tuple[bool, str]:
    cmd = f"lldap-cli user del {username}"
    return _run_shell_command(cmd)