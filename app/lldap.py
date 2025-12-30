import subprocess
import logging
from .config import LLDAP_URL, LLDAP_USER, LLDAP_PASSWORD

logger = logging.getLogger(__name__)

def _run_shell_command(command: str) -> tuple[bool, str]:
    """Internal helper to execute shell commands with LLDAP login context."""
    try:
        login_cmd = f"lldap-cli -H {LLDAP_URL} -D {LLDAP_USER} -w \"{LLDAP_PASSWORD}\" login"
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

# --- FUNCIÓN MODIFICADA ---
def create_user(username: str, email: str, password: str, first_name: str, last_name: str, telegram_id: str = None) -> tuple[bool, str]:
    """
    Crea un usuario usando -f (Firstname), -l (Lastname) y -d (Displayname).
    Opcionalmente setea el atributo custom 'telegram'.
    """
    
    # Construimos el Display Name juntando nombre y apellido
    display_name = f"{first_name} {last_name}"

    # COMANDO ACTUALIZADO:
    # Añadimos -f "{first_name}" y -l "{last_name}"
    cmd_add = (
        f"lldap-cli user add {username} {email} -p \"{password}\" "
        f"-f \"{first_name}\" -l \"{last_name}\" -d \"{display_name}\""
    )
    
    success, output = _run_shell_command(cmd_add)
    
    # Si falla la creación, paramos
    if not success:
        return False, output

    # 2. Actualizar atributo custom telegram (si se ha pasado)
    if telegram_id:
        cmd_update = f"lldap-cli user update set {username} telegram '{telegram_id}'"
        success_update, output_update = _run_shell_command(cmd_update)
        if not success_update:
            logger.error(f"Usuario creado, pero error al setear telegram id: {output_update}")
            
    return True, output

def add_user_to_group(username: str, group_name: str) -> tuple[bool, str]:
    cmd = f"lldap-cli user group add {username} {group_name}"
    return _run_shell_command(cmd)

def delete_user(username: str) -> tuple[bool, str]:
    cmd = f"lldap-cli user del {username}"
    return _run_shell_command(cmd)

def find_username_by_email(email: str) -> str | None:
    success, output = _run_shell_command("lldap-cli user list")
    if not success: return None
    
    search_email = email.lower().strip()
    for line in output.splitlines():
        if search_email in line.lower():
            parts = line.split()
            if len(parts) > 0:
                return parts[0]
    return None

def update_user_password(username: str, new_password: str) -> tuple[bool, str]:
    """
    Actualiza la contraseña de un usuario existente.
    Comando: lldap-cli user update set <UID> password <VALUE>
    """
    # Importante: Envolver la contraseña en comillas simples para evitar errores de shell
    cmd = f"lldap-cli user update set {username} password '{new_password}'"
    return _run_shell_command(cmd)