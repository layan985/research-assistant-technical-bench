from pathlib import Path
import argparse, csv, gzip, numpy as np, time
P=argparse.ArgumentParser(); P.add_argument('--rows',type=int,default=5_000_000); P.add_argument('--chunk',type=int,default=200_000); a=P.parse_args()
ROOT=Path(__file__).resolve().parent; RAW=ROOT/'raw'; RAW.mkdir(exist_ok=True); out=RAW/'events.csv.gz'
rng=np.random.default_rng(20402); regions=np.array(['NORTH','CENTRAL','SOUTH','EAST']); cats=np.array(['payroll','procurement','tax','transfer'])
with gzip.open(out,'wt',newline='') as f:
    w=csv.writer(f); w.writerow(['event_id','ingest_seq','account_id','date','region','category','amount','is_reversal'])
    eid=0
    for start in range(0,a.rows,a.chunk):
        n=min(a.chunk,a.rows-start)
        for i in range(n):
            eid+=1; account=f'A{int(rng.integers(1,350001)):08d}'
            if eid%120003==0: account='bad-account'
            date=f'2025-{int(rng.integers(1,13)):02d}-{int(rng.integers(1,29)):02d}'
            row=[f'E{eid:010d}',1,account,date,str(rng.choice(regions)),str(rng.choice(cats)),round(float(rng.lognormal(6.2,1.0)),2),int(rng.random()<0.018)]
            w.writerow(row)
            if eid%250000==0: # correction duplicate
                row[1]=2; row[6]=round(row[6]*0.9,2); w.writerow(row)
print(out)
