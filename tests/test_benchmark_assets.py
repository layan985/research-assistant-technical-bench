from pathlib import Path
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
def test_prompts_exist():
    for i,name in [(1,'data_wrangle'),(2,'large_data'),(3,'event_study'),(4,'scraping'),(5,'text_data'),(6,'bug_hunt')]:
        assert (ROOT/f'exams/task{i:02d}_{name}/PROMPT.md').exists()
def test_task01_raw_shape():
    p=ROOT/'exams/task01_data_wrangle/raw/employment.csv'
    if p.exists():
        d=pd.read_csv(p); assert len(d)>1600; assert {'firm_key','quarter','employees','correction_ts'}<=set(d.columns)
def test_task03_panel():
    p=ROOT/'exams/task03_event_study/raw/panel.csv'
    if p.exists():
        d=pd.read_csv(p); assert d.unit_id.nunique()==120; assert d.period.nunique()==30
def test_task06_has_duplicate_covariate_key():
    p=ROOT/'exams/task06_bug_hunt/raw/covariates.csv'
    if p.exists():
        d=pd.read_csv(p); assert d.duplicated(['firm_id','year']).any()
