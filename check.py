"""Comprobación independiente de API (R01, R02, R03), sin dependencias extra.

La confirmación opcional de navegador es una observación declarada: no sustituye
una prueba visual automatizada ni debe registrarse sin ejecutar el flujo real.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import time
from datetime import datetime, timezone
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

ROOT = Path(__file__).resolve().parent
OUT = ROOT / '.evidence' / 'check.json'
APP = ROOT / 'app'


def fingerprint():
    h = hashlib.sha256()
    for p in sorted(APP.rglob('*')):
        if not p.is_file() or p.is_symlink() or '__pycache__' in p.parts or p.suffix not in ('.py','.js','.html','.css'):
            continue
        h.update(p.relative_to(APP).as_posix().encode('utf-8'))
        h.update(p.read_bytes())
    return h.hexdigest()


def http(base, method, path, payload=None):
    raw = json.dumps(payload).encode() if payload is not None else None
    req = Request(base + path, data=raw, method=method, headers={'Content-Type':'application/json'})
    try:
        with urlopen(req, timeout=2) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            return resp.status, data
    except HTTPError as e:
        try:
            data = json.loads(e.read().decode('utf-8'))
        except (ValueError, UnicodeDecodeError):
            data = None
        return e.code, data


def valid_error(result, expected):
    status, data = result
    return status == expected and isinstance(data, dict) and bool(data.get('error') or data.get('message'))


def run_checks(base):
    checks = {}
    issues = []
    try:
        stat, tasks = http(base, 'GET', '/api/tasks')
        checks['R01_list'] = stat == 200 and isinstance(tasks, list) and all(isinstance(t, dict) and {'id','title','done'} <= set(t) for t in tasks)
        stat, created = http(base, 'POST', '/api/tasks', {'title':'Comprobación original'})
        checks['R02_create'] = stat == 201 and isinstance(created, dict) and created.get('title') == 'Comprobación original'
        if checks['R02_create']:
            stat, listed = http(base, 'GET', '/api/tasks')
            checks['R02_create'] = stat == 200 and any(isinstance(t, dict) and t.get('id') == created['id'] for t in listed)
        checks['R02_blank'] = valid_error(http(base, 'POST', '/api/tasks', {'title':'   '}), 400)
        checks['R03_update'] = False
        checks['R03_blank'] = False
        checks['R03_missing'] = False
        if checks['R02_create']:
            task_id = created['id']
            stat, updated = http(base, 'PUT', f'/api/tasks/{task_id}', {'title':'Título cambiado por prueba'})
            checks['R03_update'] = stat == 200 and isinstance(updated,dict) and updated.get('id') == task_id and updated.get('title') == 'Título cambiado por prueba' and 'done' in updated
            if checks['R03_update']:
                stat, listed = http(base, 'GET', '/api/tasks')
                checks['R03_update'] = stat == 200 and any(t.get('id') == task_id and t.get('title') == 'Título cambiado por prueba' for t in listed if isinstance(t,dict))
            checks['R03_blank'] = valid_error(http(base,'PUT',f'/api/tasks/{task_id}', {'title':'  '}),400)
            checks['R03_missing'] = valid_error(http(base,'PUT','/api/tasks/987654321', {'title':'X'}),404)
    except Exception as e:
        issues.append(f'Error de validación: {type(e).__name__}: {str(e)[:140]}')
    return checks, issues


def main():
    p = argparse.ArgumentParser(description='Comprueba R01/R02/R03 por HTTP en un servidor aislado')
    p.add_argument('--confirm-ui', action='store_true', help='Solo tras abrir el navegador y verificar crear > editar > guardar > recargar')
    p.add_argument('--ui-note', default='', help='Breve evidencia de lo observado durante la comprobación UI')
    args = p.parse_args()
    with socket.socket() as s:
        s.bind(('127.0.0.1',0))
        port = s.getsockname()[1]
    env=os.environ.copy()
    env['SPRINTDESK_PORT'] = str(port)
    proc = subprocess.Popen([sys.executable, str(APP/'backend'/'server.py')], cwd=ROOT, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    base=f'http://127.0.0.1:{port}'
    ready=False
    try:
        for _ in range(40):
            if proc.poll() is not None:
                break
            try:
                status, _=http(base,'GET','/api/health')
                if status==200:
                    ready=True
                    break
            except (URLError, TimeoutError, ConnectionError):
                time.sleep(.1)
        if ready:
            checks, issues=run_checks(base)
        else:
            checks, issues={}, ['No se pudo iniciar el backend de pruebas']
    finally:
        if proc.poll() is None:
            proc.terminate()
        try:
            proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            proc.kill()
    r01 = checks.get('R01_list', False)
    r02 = checks.get('R02_create', False) and checks.get('R02_blank',False)
    r03_api = all(checks.get(k, False) for k in ('R03_update', 'R03_blank', 'R03_missing'))
    sha = fingerprint()
    ui_record = None
    if OUT.exists():
        try:
            past=json.loads(OUT.read_text(encoding='utf8'))
            prev=past.get('ui_confirmation')
            if isinstance(prev,dict) and prev.get('app_sha256')==sha:
                ui_record=prev
        except (ValueError,OSError):
            pass
    if args.confirm_ui:
        if not args.ui_note.strip():
            issues.append('Se omitió --confirm-ui porque no se proporcionó --ui-note')
        elif not r03_api:
            issues.append('Se omitió --confirm-ui porque R03 API no pasó')
        else:
            ui_record={
                'app_sha256':sha,
                'checked_at':datetime.now(timezone.utc).isoformat(),
                'method':'declaración de prueba en navegador (no prueba E2E independiente)',
                'note':args.ui_note.strip()[:400],
            }
    verified_count=int(r01)+int(r02)+int(r03_api and ui_record is not None)
    result={
        'timestamp':datetime.now(timezone.utc).isoformat(),
        'app_sha256':sha,
        'checks':checks,
        'requirements':{'R01':bool(r01),'R02':bool(r02),'R03_API':bool(r03_api),'R03_UI_confirmada':ui_record is not None},
        'verified_count':verified_count,
        'percent':verified_count*10,
        'ui_confirmation':ui_record,
        'issues':issues,
    }
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    for name, passed in checks.items():
        print(f"{'OK' if passed else 'PENDIENTE'}  {name}")
    print(f'Progreso verificado: {verified_count}/10 ({verified_count*10}%). R03 API={r03_api}; UI confirmada={ui_record is not None}')
    for issue in issues:print('AVISO',issue)
    print('Resultados:', OUT.relative_to(ROOT))
    # Un R03 aún pendiente es esperado en la versión inicial, así que no es fallo del script.
    return 0 if r01 and r02 else 1


if __name__=='__main__':
    raise SystemExit(main())
