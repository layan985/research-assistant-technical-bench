from pathlib import Path
import argparse, json, random
from reportlab.pdfgen import canvas
P=argparse.ArgumentParser(); P.add_argument('--documents',type=int,default=10000); a=P.parse_args()
ROOT=Path(__file__).resolve().parent; ARC=ROOT/'archive'; DOC=ARC/'docs'; DOC.mkdir(parents=True,exist_ok=True)
random.seed(40404); agencies=['Ministry of Finance','Labor Bureau','Trade Authority','Statistics Office']; types=['notice','report','circular','bulletin']
manifest=[]
for i in range(1,a.documents+1):
    did=f'GOV-{i:06d}'; rev=2 if i%997==0 else 1; agency=agencies[i%4]; typ=types[i%4]
    y=2024+(i%2); m=1+(i%12); d=1+(i%27); date_forms=[f'{y}-{m:02d}-{d:02d}',f'{d:02d}/{m:02d}/{y}',f'{m:02d}-{d:02d}-{y}']; date=date_forms[i%3]
    title='' if i%613==0 else f'{typ.title()} {did}'
    if i%10==0:
        fn=f'{did}.pdf'; p=DOC/fn; c=canvas.Canvas(str(p)); c.setTitle(title or did); c.setAuthor(agency); c.drawString(72,750,f'Document ID: {did}'); c.drawString(72,730,f'Title: {title}'); c.drawString(72,710,f'Date: {date}'); c.drawString(72,690,f'Agency: {agency}'); c.drawString(72,670,f'Type: {typ}'); c.drawString(72,650,f'Revision: {rev}'); c.save(); kind='pdf'
    else:
        fn=f'{did}.html'; p=DOC/fn
        if i%701==0: html=f'<html><head><title>{title}</title></head><body><div data-id="{did}"><span class="agency">{agency}'
        else: html=(f'<html><head><title>{title}</title></head><body>'
                    f'<article data-id="{did}" data-revision="{rev}"><h1>{title}</h1>'
                    f'<time>{date}</time><span class="agency">{agency}</span>'
                    f'<span class="doctype">{typ}</span></article></body></html>')
        p.write_text(html,encoding='utf-8'); kind='html'
    url_path=(f'/redirect/{fn}' if i%503==0 else f'/docs/{fn}')
    manifest.append({'document_id':did,'path':url_path,'title':title,'published_date':date,'agency':agency,'document_type':typ,'revision':rev,'kind':kind})
for base in [x for x in [997,1994,2991,3988,4985] if x <= a.documents]:
    did=f'GOV-{base:06d}'; fn=f'{did}-rev3.html'; agency=agencies[base%4]; typ=types[base%4]; title=f'{typ.title()} {did} revised'; date='2025-12-31'; rev=3
    (DOC/fn).write_text(f'<article data-id="{did}" data-revision="3"><h1>{title}</h1><time>{date}</time><span class="agency">{agency}</span><span class="doctype">{typ}</span></article>',encoding='utf-8')
    manifest.append({'document_id':did,'path':f'/docs/{fn}','title':title,'published_date':date,'agency':agency,'document_type':typ,'revision':rev,'kind':'html'})
(ARC/'manifest.json').write_text(json.dumps(manifest,indent=2))
index='\n'.join(f'<a href="{x["path"]}">{x["document_id"]}</a><br>' for x in manifest)
(ARC/'index.html').write_text(index,encoding='utf-8')
print(f'Generated {len(manifest)} URLs in {ARC}')
