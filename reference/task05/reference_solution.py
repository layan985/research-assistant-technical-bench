from pathlib import Path
import pandas as pd, numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import TruncatedSVD
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score, accuracy_score
ROOT=Path(__file__).resolve().parents[2]; df=pd.read_csv(ROOT/'exams/task05_text_data/raw/generated_documents.csv')
tr=df.template_family%5!=0; te=~tr
v=TfidfVectorizer(ngram_range=(1,2),min_df=2,max_features=12000); X=v.fit_transform(df.loc[tr,'text']); Xt=v.transform(df.loc[te,'text'])
svd=TruncatedSVD(n_components=64,random_state=50505); E=svd.fit_transform(X); Et=svd.transform(Xt)
for target in ['topic','sentiment']:
    m=LogisticRegression(max_iter=500).fit(E,df.loc[tr,target]); p=m.predict(Et)
    print(target,'acc',accuracy_score(df.loc[te,target],p),'macro_f1',f1_score(df.loc[te,target],p,average='macro'))
