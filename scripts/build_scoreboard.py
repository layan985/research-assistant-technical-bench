from pathlib import Path
import csv, json
ROOT=Path(__file__).resolve().parents[1]
rows=[]
for f in sorted((ROOT/'attempts').glob('task*/**/GRADE.json')):
    g=json.loads(f.read_text()); a=json.loads((f.parent/'ATTEMPT.json').read_text())
    rows.append({'task':a['task'],'attempt':f.parent.name,'minutes':a.get('elapsed_minutes'),'score':g.get('score'),'status':'OVERTIME' if (a.get('elapsed_minutes') or 1e9)>90 else 'ON_TIME','critical_fail':g.get('critical_fail',False)})
out=ROOT/'scoreboard/results/scoreboard.csv'; out.parent.mkdir(parents=True,exist_ok=True)
with out.open('w',newline='') as fh:
    wr=csv.DictWriter(fh,fieldnames=['task','attempt','minutes','score','status','critical_fail']); wr.writeheader(); wr.writerows(rows)
print(out)
