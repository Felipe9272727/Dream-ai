"""
💾 Armazenamento persistente — SEMPRE salva no Google Drive quando disponível.

A Dream-AI "vive entre sessões", mas o Colab APAGA tudo ao desligar. Para a vida dela
ser realmente contínua, todo artefato importante (identidade, memória, checkpoints,
adapters) é salvo no Google Drive.

Como funciona a raiz de armazenamento (em ordem de prioridade):
  1. Variável de ambiente DREAM_HOME, se definida.
  2. Google Drive montado (/content/drive/MyDrive) → usa <Drive>/DreamAI.
  3. Diretório local (.) como último recurso.

No Colab, chame `mount_drive()` uma vez no início para montar o Drive.
"""

from __future__ import annotations

import os

DRIVE_MOUNT = "/content/drive"
DRIVE_ROOT = os.path.join(DRIVE_MOUNT, "MyDrive")
APP_FOLDER = "DreamAI"  # pasta da IA dentro do Drive


def mount_drive(force: bool = False) -> bool:
    """Monta o Google Drive (só funciona no Colab). Retorna True se montado."""
    if os.path.isdir(DRIVE_ROOT) and not force:
        return True
    try:
        from google.colab import drive  # type: ignore

        drive.mount(DRIVE_MOUNT, force_remount=force)
        os.makedirs(home(), exist_ok=True)
        print(f"💾 Google Drive montado. Tudo será salvo em: {home()}")
        return True
    except Exception as e:  # noqa: BLE001
        print(f"⚠️  Não foi possível montar o Drive ({e}). Usando armazenamento local.")
        return False


def home() -> str:
    """Diretório raiz onde TUDO é salvo. Detecta o Drive automaticamente."""
    env = os.environ.get("DREAM_HOME")
    if env:
        return env
    if os.path.isdir(DRIVE_ROOT):
        return os.path.join(DRIVE_ROOT, APP_FOLDER)
    return os.getcwd()


def resolve(*parts: str) -> str:
    """Resolve um caminho dentro da raiz de armazenamento, criando a pasta pai."""
    path = os.path.join(home(), *parts)
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    return path


def is_on_drive() -> bool:
    """True se estamos de fato salvando no Google Drive."""
    return home().startswith(DRIVE_ROOT) or os.environ.get("DREAM_HOME", "").startswith(DRIVE_ROOT)


def status() -> str:
    local = "Google Drive ☁️" if is_on_drive() else "local (efêmero ⚠️)"
    return f"Armazenamento: {local} → {home()}"
