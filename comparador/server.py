"""Servidor local del comparador: archivos de app frente al baseline. Solo stdlib."""
from pathlib import Path
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs
import difflib
import json
import os

ROOT=Path(__file__).resolve().parent.parent
BEFORE=ROOT/'.baseline'/'app'
AFTER=ROOT/'app'
WEB=ROOT/'comparador'/'web'
REPORT=ROOT/'.evidence'/'check.json'
EXTS={'.py','.js','.html','.css','.json','.md'}
EXCLUDE={'.git','__pycache__','node_modules','.venv','dist','.evidence'}


def files_in(root):
    items=set()
    for f in root.rglob('*'):
        if not f.is_file() or f.is_symlink() or f.suffix.lower() not in EXTS:
            continue
        r=f.relative_to(root)
        if any(part in EXCLUDE for part in r.parts) or f.stat().st_size>130000:
            continue
        items.add(r.as_posix())
    return items


def text_in(root, relative):
    path=(root/relative).resolve()
    if not path.is_relative_to(root.resolve()) or not path.is_file() or path.is_symlink() or path.stat().st_size>130000:
        return ''
    return path.read_text(encoding='utf8',errors='replace')


def current_state():
    all_files=sorted(files_in(BEFORE)|files_in(AFTER))[:200]
    result=[]
    added_total=removed_total=0
    for r in all_files:
        a=text_in(BEFORE,r).splitlines()
        b=text_in(AFTER,r).splitlines()
        ops=difflib.SequenceMatcher(None,a,b,autojunk=False).get_opcodes()
        plus=sum(j2-j1 for tag,i1,i2,j1,j2 in ops if tag in ('insert','replace'))
        minus=sum(i2-i1 for tag,i1,i2,j1,j2 in ops if tag in ('delete','replace'))
        status='modificado' if plus+minus else 'sin cambios'
        if not (BEFORE/r).exists():status='nuevo'
        if not (AFTER/r).exists():status='eliminado'
        result.append({'path':r,'status':status,'plus':plus,'minus':minus})
        added_total+=plus;removed_total+=minus
    verification=None
    if REPORT.exists():
        try:
            verification=json.loads(REPORT.read_text(encoding='utf8'))
            # Verificar que no se haya alterado la aplicación después de producir el reporte.
            import hashlib
            h=hashlib.sha256()
            for f in sorted(AFTER.rglob('*')):
                if f.is_file() and not f.is_symlink() and '__pycache__' not in f.parts and f.suffix in ('.py','.js','.html','.css'):
                    h.update(f.relative_to(AFTER).as_posix().encode('utf8'))
                    h.update(f.read_bytes())
            if verification.get('app_sha256') != h.hexdigest():
                verification={'stale':True}
        except (OSError,ValueError):
            verification=None
    return {'files':result,'changed':sum(x['status']!='sin cambios' for x in result), 'added':added_total,'removed':removed_total, 'verification':verification}


def diff_of(rel):
    all_files=files_in(BEFORE)|files_in(AFTER)
    if rel not in all_files:
        raise ValueError('Archivo no permitido')
    before=text_in(BEFORE,rel).splitlines()
    after=text_in(AFTER,rel).splitlines()
    rows=[]
    for t,i1,i2,j1,j2 in difflib.SequenceMatcher(None,before,after,autojunk=False).get_opcodes():
        count=max(i2-i1,j2-j1)
        for k in range(count):
            rows.append({'kind':t,'before':before[i1+k] if i1+k<i2 else '', 'after':after[j1+k] if j1+k<j2 else '', 'bl':i1+k+1 if i1+k<i2 else None,'al':j1+k+1 if j1+k<j2 else None})
    return rows[:2500]


class Handler(BaseHTTPRequestHandler):
    def reply(self,status,payload):
        data=json.dumps(payload,ensure_ascii=False).encode('utf8')
        self.send_response(status)
        self.send_header('Content-Type','application/json; charset=utf-8')
        self.send_header('Cache-Control','no-store')
        self.send_header('Content-Length',str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        parsed=urlparse(self.path)
        if parsed.path=='/api/state':
            return self.reply(200,current_state())
        if parsed.path=='/api/diff':
            rel=parse_qs(parsed.query).get('file',[''])[0]
            try:
                return self.reply(200,{'rows':diff_of(rel)})
            except ValueError as ex:
                return self.reply(400,{'error':str(ex)})
        static={'/':'index.html','/main.js':'main.js','/style.css':'style.css'}
        if parsed.path in static:
            fname=static[parsed.path]
            body=(WEB/fname).read_bytes()
            mime='text/html' if fname.endswith('.html') else 'text/javascript' if fname.endswith('.js') else 'text/css'
            self.send_response(200)
            self.send_header('Content-Type',mime+'; charset=utf-8')
            self.send_header('Cache-Control','no-store')
            self.send_header('Content-Length',str(len(body)))
            self.end_headers()
            return self.wfile.write(body)
        return self.reply(404,{'error':'No encontrado'})


def run():
    addr=('127.0.0.1',int(os.environ.get('GUARDIAN_COMPARE_PORT','8766')))
    server=ThreadingHTTPServer(addr,Handler)
    print(f'Comparador web: http://{addr[0]}:{addr[1]}',flush=True)
    server.serve_forever()


if __name__=='__main__':
    run()
