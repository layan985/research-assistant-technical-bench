from pathlib import Path
import numpy as np, pandas as pd, random
ROOT=Path(__file__).resolve().parent; RAW=ROOT/'raw'; RAW.mkdir(exist_ok=True)
rng=np.random.default_rng(10401); random.seed(10401)
firms=[f'F{i:04d}' for i in range(1,201)]
regions=['North','Central','South','East']
master=pd.DataFrame({'firm_id':firms,'legal_name':[f'Orion Industries {i:03d}' for i in range(1,201)],'region_code':[regions[i%4][0] for i in range(200)]})
master=pd.concat([master, master.iloc[[7]].assign(legal_name='Orion Industries 008 Ltd')],ignore_index=True)
master.to_csv(RAW/'firm_master.csv',index=False)

def messy(fid,i):
    n=int(fid[1:]); forms=[fid.lower(),fid.replace('F','F-'),f' {n:04d} ',f'firm_{n:04d}',fid]
    return forms[i%len(forms)]
quarters=pd.period_range('2024Q1','2025Q4',freq='Q')
emp=[]; fin=[]
for fi,f in enumerate(firms):
  base=30+(fi%70)
  for qi,q in enumerate(quarters):
    qforms=[str(q),f'{q.year}-Q{q.quarter}',str(q.end_time.date())]
    emp.append([messy(f,fi+qi),qforms[(fi+qi)%3],base+qi+(fi%5),f'2026-01-{(qi%9)+1:02d}'])
    rev=(base*100000)*(1+0.03*qi)+rng.normal(0,30000)
    fin.append([messy(f,fi+qi+2),qforms[(fi+qi+1)%3],f'${rev:,.2f}',f'2026-02-{(qi%9)+1:02d}'])
# duplicate correction rows: later timestamp should win
for idx in [13,144,777,1211]:
    r=emp[idx].copy(); r[2]=int(r[2])+3; r[3]='2026-03-20'; emp.append(r)
for idx in [31,402,999]:
    r=fin[idx].copy(); num=float(r[2].replace('$','').replace(',',''))+5000; r[2]=f'${num:,.2f}'; r[3]='2026-03-21'; fin.append(r)
# malformed identifiers and missing values
emp.append(['UNKNOWN-X','2024Q1',99,'2026-02-01'])
fin.append(['','2024Q2','$100,000.00','2026-02-01'])
pd.DataFrame(emp,columns=['firm_key','quarter','employees','correction_ts']).to_csv(RAW/'employment.csv',index=False)
pd.DataFrame(fin,columns=['company_identifier','period','revenue','correction_ts']).to_csv(RAW/'financials.csv',index=False)
# adoption: 120 adopters, plus duplicate and invalid event
ad=[]
for fi,f in enumerate(firms[:120]):
    aq=quarters[2+(fi%5)]
    ad.append([messy(f,fi),str(aq.start_time.date()),'verified'])
ad += [ad[10], ['bad-id','2024-06-01','verified'], [messy(firms[150],150),'not-a-date','verified']]
pd.DataFrame(ad,columns=['entity_id','adoption_date','status']).to_csv(RAW/'ai_adoption.csv',index=False)
reg=pd.DataFrame({'region_code':['N','C','S','E'],'region_name':['North','Central ','south','EAST']})
reg.to_csv(RAW/'regions.csv',index=False)
print(f'generated {RAW}')
