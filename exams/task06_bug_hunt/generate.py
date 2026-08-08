from pathlib import Path
import numpy as np, pandas as pd
ROOT=Path(__file__).resolve().parent; RAW=ROOT/'raw'; BROKEN=ROOT/'broken'; RAW.mkdir(exist_ok=True); BROKEN.mkdir(exist_ok=True)
rng=np.random.default_rng(60606); rows=[]; cov=[]
for firm in range(1,301):
    tp=2022 if firm<=150 else 9999; alpha=rng.normal()
    for year in range(2018,2026):
        age=17+(firm%40); sales=max(0,rng.lognormal(7,0.6)-500)
        treated_post=int(year>=tp); mediator=0.6*treated_post+rng.normal(0,0.5)
        y=alpha+0.25*(year-2018)+1.2*treated_post+0.15*np.log1p(sales)+rng.normal(0,1)
        rows.append([firm,year,age,sales,treated_post,mediator,y])
        cov.append([firm,year,firm%5,0.1*(firm%7)+rng.normal(0,.1)])
cov.append([10,2020,0,99.0])
pd.DataFrame(rows,columns=['firm_id','year','age','sales','treated_post','mediator','outcome']).to_csv(RAW/'outcomes.csv',index=False)
pd.DataFrame(cov,columns=['firm_id','year','industry','baseline_score']).to_csv(RAW/'covariates.csv',index=False)
