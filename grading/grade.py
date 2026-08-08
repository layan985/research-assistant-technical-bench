from pathlib import Path
import argparse, json, re, pandas as pd, numpy as np
ROOT=Path(__file__).resolve().parents[1]

def attempt_path(task, val):
    base=ROOT/'attempts'/f'task{task}'
    if val!='latest': return base/val
    ds=sorted(p for p in base.glob('*') if p.is_dir())
    if not ds: raise SystemExit('No attempts')
    return ds[-1]

def exists_score(out, names, per): return sum(per for n in names if (out/n).exists())

def grade01(out):
    req=['panel.csv','summary_stats.csv','exclusions.csv','data_quality.json','README.md','run.py']; score=exists_score(out,req,3)
    critical=False; notes=[]
    if (out/'panel.csv').exists():
        p=pd.read_csv(out/'panel.csv'); exp={'firm_id','quarter','region','employees','revenue_usd','ai_adopted'}
        score+=12 if exp.issubset(p.columns) else 0
        score+=10 if not p.duplicated(['firm_id','quarter']).any() else 0
        score+=10 if len(p)==1600 else max(0,10-abs(len(p)-1600)/20)
        score+=5 if p.firm_id.nunique()==200 else 0
        score+=5 if set(pd.to_numeric(p.ai_adopted,errors='coerce').dropna().unique()).issubset({0,1}) else 0
        ok=True
        for _,g in p.sort_values(['firm_id','quarter']).groupby('firm_id'):
            a=g.ai_adopted.fillna(0).astype(int).to_numpy(); ok &= np.all(np.diff(a)>=0)
        score+=8 if ok else 0
    score+=15 if (out/'run.py').exists() else 0; score+=7 if (out/'README.md').exists() else 0; score+=10 if (out/'exclusions.csv').exists() else 0
    return min(100,round(score,2)),critical,notes

def grade02(out):
    req=['daily_region_summary.parquet','account_summary.parquet','quality.json','query.sql','run.py','README.md']
    score=exists_score(out,req,10); critical=False; notes=[]

    q={}
    if (out/'quality.json').exists():
        try: q=json.loads((out/'quality.json').read_text())
        except Exception as e: notes.append(f'quality.json unreadable: {e}')
        score += 4 if q.get('input_rows')==5_000_020 else 0
        score += 4 if q.get('duplicate_event_ids_removed')==20 else 0
        score += 4 if q.get('invalid_account_rows_excluded')==41 else 0
        peak=q.get('peak_rss_mb')
        score += 4 if isinstance(peak,(int,float)) and peak < 1500 else 0

    expected_clean=4_999_959
    if (out/'daily_region_summary.parquet').exists():
        try:
            d=pd.read_parquet(out/'daily_region_summary.parquet')
            needed={'date','region','n_events','n_accounts','gross_amount','net_amount'}
            score += 4 if needed.issubset(d.columns) else 0
            score += 4 if needed.issubset(d.columns) and not d.duplicated(['date','region']).any() and int(d['n_events'].sum())==expected_clean else 0
            if needed.issubset(d.columns) and float(d['net_amount'].sum()) >= float(d['gross_amount'].sum()):
                notes.append('net amount does not reflect reversal signing')
        except Exception as e: notes.append(f'daily parquet unreadable: {e}')

    if (out/'account_summary.parquet').exists():
        try:
            a=pd.read_parquet(out/'account_summary.parquet')
            needed={'account_id','n_events','net_amount'}
            score += 4 if needed.issubset(a.columns) else 0
            valid = needed.issubset(a.columns) and a['account_id'].astype(str).str.fullmatch(r'A\d{8}').all()
            consistent = needed.issubset(a.columns) and int(a['n_events'].sum())==expected_clean and not a.duplicated('account_id').any()
            score += 4 if valid and consistent else 0
        except Exception as e: notes.append(f'account parquet unreadable: {e}')

    run_txt=(out/'run.py').read_text().lower() if (out/'run.py').exists() else ''
    sql_txt=(out/'query.sql').read_text().lower() if (out/'query.sql').exists() else ''
    uses_duckdb='duckdb' in run_txt
    full_pandas=('pandas.read_csv' in run_txt or 'pd.read_csv' in run_txt)
    latest_ingest=bool(re.search(r'row_number\s*\(\s*\)\s*over',sql_txt,re.S)) and 'ingest_seq' in sql_txt and 'desc' in sql_txt
    reversal_signed=('is_reversal' in sql_txt and ('-amount' in sql_txt or '- amount' in sql_txt))
    if uses_duckdb and not full_pandas and latest_ingest and reversal_signed:
        score += 8
    else:
        if not uses_duckdb: notes.append('run.py does not use DuckDB')
        if full_pandas: notes.append('critical: full pandas CSV load detected')
        if not latest_ingest: notes.append('critical: latest ingest-sequence deduplication not evident in SQL')
        if not reversal_signed: notes.append('critical: reversal signing not evident in SQL')
        critical = full_pandas or not latest_ingest or not reversal_signed

    return min(100,round(score,2)),critical,notes

def grade_generic(task,out):
    contracts={
    '03':['event_study.csv','event_study.png','regression_notes.md','run.py','robustness.csv'],
    '04':['documents.parquet','failures.csv','quality.json','run.py','README.md'],
    '05':['predictions.parquet','embeddings.parquet','metrics.json','model_card.md','run.py'],
    '06':['FIX_LOG.md','analysis_fixed.R','analysis_fixed.do','results.csv']}
    files=contracts[task]; score=exists_score(out,files,10); notes=[]; critical=False
    if task=='03' and (out/'event_study.csv').exists():
        d=pd.read_csv(out/'event_study.csv'); needed={'event_time','estimate','std_error','ci_low','ci_high'}
        score+=20 if needed.issubset(d.columns) else 0; score+=10 if -1 not in set(d.get('event_time',[])) else 0
    elif task=='04' and (out/'documents.parquet').exists():
        d=pd.read_parquet(out/'documents.parquet'); score+=20 if d.document_id.nunique()>=9950 else 0; score+=10 if not d.duplicated('document_id').any() else 0
    elif task=='05' and (out/'metrics.json').exists():
        m=json.loads((out/'metrics.json').read_text()); vals=[v for v in m.values() if isinstance(v,(int,float))]; score+=20 if vals and max(vals)<=1.0001 else 0
        if (out/'embeddings.parquet').exists():
            e=pd.read_parquet(out/'embeddings.parquet'); score+=10 if len([c for c in e if c.startswith('e')])>=32 else 0
    elif task=='06' and (out/'FIX_LOG.md').exists():
        txt=(out/'FIX_LOG.md').read_text().lower(); keywords=['merge','age','log','cluster','year','mediator','lag','unmatched']; score+=min(30,4*sum(k in txt for k in keywords))
    else: score+=10
    return min(100,round(score,2)),critical,notes

p=argparse.ArgumentParser(); p.add_argument('task',choices=[f'{i:02d}' for i in range(1,7)]); p.add_argument('--attempt',default='latest'); a=p.parse_args(); path=attempt_path(a.task,a.attempt); out=path/'outputs'
if a.task=='01': score,critical,notes=grade01(out)
elif a.task=='02': score,critical,notes=grade02(out)
else: score,critical,notes=grade_generic(a.task,out)
result={'task':a.task,'score':score,'critical_fail':critical,'notes':notes}; (path/'GRADE.json').write_text(json.dumps(result,indent=2)); print(json.dumps(result,indent=2))
