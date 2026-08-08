from pathlib import Path
import pandas as pd, statsmodels.formula.api as smf
ROOT=Path(__file__).resolve().parents[2]
df=pd.read_csv(ROOT/'exams/task03_event_study/raw/panel.csv')
df['event_time']=df['period']-df['treat_period']
terms=[]
for k in range(-5,7):
    if k==-1: continue
    name=f'event_m{abs(k)}' if k<0 else f'event_p{k}'
    df[name]=((df.event_time==k)&df.treated.astype(bool)).astype(int); terms.append((k,name))
f='y ~ '+' + '.join(n for _,n in terms)+' + C(unit_id) + C(period)'
m=smf.ols(f,df).fit(cov_type='cluster',cov_kwds={'groups':df.unit_id})
out=[]
for k,n in terms:
    b=m.params[n]; se=m.bse[n]; out.append([k,b,se,b-1.96*se,b+1.96*se])
print(pd.DataFrame(out,columns=['event_time','estimate','std_error','ci_low','ci_high']).to_string(index=False))
