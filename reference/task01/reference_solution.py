from pathlib import Path
import pandas as pd, re, json
ROOT=Path(__file__).resolve().parents[2]; RAW=ROOT/'exams/task01_data_wrangle/raw'
def norm_id(x):
    s=str(x).strip().upper(); d=''.join(ch for ch in s if ch.isdigit())
    return f'F{int(d):04d}' if d else None
def norm_q(x):
    try:
        s=str(x).strip().upper().replace('-Q','Q')
        if 'Q' in s: return str(pd.Period(s,freq='Q'))
        return str(pd.Period(pd.to_datetime(s),freq='Q'))
    except: return None
master=pd.read_csv(RAW/'firm_master.csv').drop_duplicates('firm_id',keep='first')
regions=pd.read_csv(RAW/'regions.csv'); regions['region_name']=regions.region_name.str.strip().str.title()
master=master.merge(regions,on='region_code',how='left')
emp=pd.read_csv(RAW/'employment.csv'); emp['firm_id']=emp.firm_key.map(norm_id); emp['quarter']=emp.quarter.map(norm_q); emp['correction_ts']=pd.to_datetime(emp.correction_ts)
emp=emp.sort_values('correction_ts').drop_duplicates(['firm_id','quarter'],keep='last')
fin=pd.read_csv(RAW/'financials.csv'); fin['firm_id']=fin.company_identifier.map(norm_id); fin['quarter']=fin.period.map(norm_q); fin['correction_ts']=pd.to_datetime(fin.correction_ts); fin['revenue_usd']=fin.revenue.str.replace(r'[$,]','',regex=True).astype(float)
fin=fin.sort_values('correction_ts').drop_duplicates(['firm_id','quarter'],keep='last')
ad=pd.read_csv(RAW/'ai_adoption.csv'); ad['firm_id']=ad.entity_id.map(norm_id); ad['adoption_date']=pd.to_datetime(ad.adoption_date,errors='coerce'); ad=ad[(ad.status=='verified')&ad.firm_id.isin(master.firm_id)&ad.adoption_date.notna()]
first=ad.groupby('firm_id').adoption_date.min().to_dict()
quarters=[str(q) for q in pd.period_range('2024Q1','2025Q4',freq='Q')]
panel=pd.MultiIndex.from_product([master.firm_id,quarters],names=['firm_id','quarter']).to_frame(index=False)
panel=panel.merge(master[['firm_id','region_name']],on='firm_id',how='left').rename(columns={'region_name':'region'})
panel=panel.merge(emp[['firm_id','quarter','employees']],on=['firm_id','quarter'],how='left').merge(fin[['firm_id','quarter','revenue_usd']],on=['firm_id','quarter'],how='left')
panel['ai_adopted']=[int(fid in first and pd.Period(q,freq='Q').end_time >= first[fid]) for fid,q in zip(panel.firm_id,panel.quarter)]
print(panel.head())
