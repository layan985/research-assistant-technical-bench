from pathlib import Path
import argparse, datetime as dt, json, shutil, subprocess
ROOT=Path(__file__).resolve().parents[1]
TASKS={f'{i:02d}':f'task{i:02d}' for i in range(1,7)}

def git_sha():
    try: return subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True,stderr=subprocess.DEVNULL).strip()
    except Exception: return None

p=argparse.ArgumentParser(); p.add_argument('task', choices=TASKS); args=p.parse_args()
now=dt.datetime.now().astimezone(); stamp=now.strftime('%Y%m%dT%H%M%S%z')
out=ROOT/'attempts'/TASKS[args.task]/stamp
(out/'work').mkdir(parents=True)
(out/'outputs').mkdir()
meta={'task':args.task,'started_at':now.isoformat(),'submitted_at':None,'elapsed_minutes':None,'git_sha_start':git_sha(),'status':'RUNNING'}
(out/'ATTEMPT.json').write_text(json.dumps(meta,indent=2))
(out/'work/README.md').write_text('# Candidate work\n\nPut all code here. Final deliverables go in `../outputs/`.\n')
print(out)
print('CLOCK STARTED. Target: 90 minutes.')
