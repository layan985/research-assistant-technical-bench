from pathlib import Path
import argparse, random, pandas as pd
P=argparse.ArgumentParser(); P.add_argument('--documents',type=int,default=20000); a=P.parse_args()
ROOT=Path(__file__).resolve().parent; RAW=ROOT/'raw'; RAW.mkdir(exist_ok=True)
random.seed(50505)
topics={
'labor':['employment','wages','workers','firms','jobs'],
'health':['hospitals','patients','clinics','health','medicine'],
'education':['schools','students','teachers','education','curriculum'],
'taxation':['tax','revenue','fiscal','levy','income'],
'trade':['exports','imports','tariff','trade','customs']}
sent={'positive':['improved','expanded','strong','beneficial'],'neutral':['reported','recorded','scheduled','observed'],'negative':['declined','weakened','delayed','adverse']}
rows=[]; tnames=list(topics); snames=list(sent)
for i in range(a.documents):
    fam=i%400; topic=tnames[(i//400)%len(tnames)]; sentiment=snames[(i//37)%3]
    kw=random.sample(topics[topic],3); sk=random.choice(sent[sentiment]); noise=random.choice(['quarterly review','administrative update','regional memorandum','technical annex'])
    text=f'{noise}. {kw[0]} and {kw[1]} conditions {sk}; the {kw[2]} program was assessed in template family {fam%20}.'
    if i%41==0: text='  '+text.upper()+'  '
    rows.append([f'D{i:06d}',fam,topic,sentiment,text])
pd.DataFrame(rows,columns=['doc_id','template_family','topic','sentiment','text']).to_csv(RAW/'generated_documents.csv',index=False)
print(RAW/'generated_documents.csv')
