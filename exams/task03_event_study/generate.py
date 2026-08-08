from pathlib import Path
import numpy as np, pandas as pd
ROOT=Path(__file__).resolve().parent; RAW=ROOT/'raw'; RAW.mkdir(exist_ok=True)
rng=np.random.default_rng(30303); units=np.arange(1,121); periods=np.arange(1,31)
rows=[]
for u in units:
    treated=u<=90; tp=(10+(u%8)) if treated else np.nan
    alpha=rng.normal(0,1); trend=(u%7)*0.003
    for t in periods:
        lam=0.05*t+0.3*np.sin(t/3)
        et=t-tp if treated else np.nan
        eff=0
        if treated and t>=tp:
            eff=0.15+0.12*min(et,6)
        y=alpha+lam+trend*t+eff+rng.normal(0,0.45)
        rows.append([u,t,tp,y,treated,int(u%4)])
pd.DataFrame(rows,columns=['unit_id','period','treat_period','y','treated','region']).to_csv(RAW/'panel.csv',index=False)
print(RAW/'panel.csv')
