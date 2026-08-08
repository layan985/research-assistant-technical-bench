from pathlib import Path
import argparse, datetime as dt, hashlib, json
ROOT=Path(__file__).resolve().parents[1]

def find_attempt(task, val):
    base=ROOT/'attempts'/f'task{task}'
    if val!='latest': return base/val
    ds=sorted([p for p in base.glob('*') if p.is_dir()])
    if not ds: raise SystemExit('No attempts found')
    return ds[-1]

def hashes(folder):
    out={}
    for p in sorted(folder.rglob('*')):
        if p.is_file():
            h=hashlib.sha256(p.read_bytes()).hexdigest(); out[str(p.relative_to(folder))]=h
    return out

p=argparse.ArgumentParser(); p.add_argument('task'); p.add_argument('--attempt',default='latest'); a=p.parse_args()
path=find_attempt(a.task,a.attempt); f=path/'ATTEMPT.json'; meta=json.loads(f.read_text())
now=dt.datetime.now().astimezone(); start=dt.datetime.fromisoformat(meta['started_at'])
meta.update(submitted_at=now.isoformat(), elapsed_minutes=round((now-start).total_seconds()/60,2), status='SUBMITTED', output_hashes=hashes(path/'outputs'))
f.write_text(json.dumps(meta,indent=2))
print(json.dumps(meta,indent=2))
