"""Inicia SprintDesk y el comparador localmente; solo biblioteca estándar."""
from pathlib import Path
import subprocess
import os
import sys
import time

ROOT = Path(__file__).resolve().parent
SCRIPTS = [ROOT / 'app' / 'backend' / 'server.py', ROOT / 'comparador' / 'server.py']


def main():
    children = []
    try:
        for script in SCRIPTS:
            children.append(subprocess.Popen([sys.executable, str(script)], cwd=ROOT))
        print(f"SprintDesk: http://127.0.0.1:{os.environ.get('SPRINTDESK_PORT','8765')}", flush=True)
        print(f"Comparador: http://127.0.0.1:{os.environ.get('GUARDIAN_COMPARE_PORT','8766')}", flush=True)
        print('Ctrl+C para cerrar los servidores.', flush=True)
        while True:
            if any(p.poll() is not None for p in children):
                print('Un servidor terminó: comprueba que los puertos 8765/8766 estén disponibles.', file=sys.stderr)
                return 1
            time.sleep(.4)
    except KeyboardInterrupt:
        return 0
    finally:
        for child in children:
            if child.poll() is None:
                child.terminate()
        for child in children:
            try:
                child.wait(timeout=3)
            except subprocess.TimeoutExpired:
                child.kill()


if __name__ == '__main__':
    raise SystemExit(main())
