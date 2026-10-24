import warnings, numpy as np, pandas as pd
warnings.filterwarnings('ignore')
from sklearn.svm import SVC
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import GridSearchCV, GroupKFold, LeaveOneGroupOut
from sklearn.metrics import accuracy_score, f1_score, matthews_corrcoef
d=pd.read_csv('soybean_growth_stage_dataset.csv')
d=pd.concat([d,pd.get_dummies(d['tillage'],prefix='till',dtype=float)],axis=1)
till=[c for c in d.columns if c.startswith('till_')]
S={
 'full (9 + tillage)':['doy','dap','plant_doy','RM','nodes_per_plant','nodes_per_dap','latitude','longitude','seeding_rate']+till,
 'no seeding/tillage':['doy','dap','plant_doy','RM','nodes_per_plant','nodes_per_dap','latitude','longitude'],
 'no site info (no lat/lon/seeding/tillage)':['doy','dap','plant_doy','RM','nodes_per_plant','nodes_per_dap'],
}
le=LabelEncoder(); y=le.fit_transform(d['stage_group']); g=d['site_id'].values
for name,cols in S.items():
    X=d[cols].values; p=np.empty(len(d),int)
    for tr,te in LeaveOneGroupOut().split(X,y,g):
        gs=GridSearchCV(Pipeline([('sc',StandardScaler()),('m',SVC())]),{'m__C':[1,10,100]},cv=GroupKFold(3),scoring='f1_macro')
        gs.fit(X[tr],y[tr],groups=g[tr]); p[te]=gs.predict(X[te])
    print(f'{name:45s} acc={accuracy_score(y,p):.3f} macroF1={f1_score(y,p,average="macro"):.3f} MCC={matthews_corrcoef(y,p):.3f}',flush=True)

# Friedman test across held-out sites (stage_group, full features)
from scipy.stats import friedmanchisquare
pr=pd.read_csv('results/predictions_stage_group_full.csv')
models=[c for c in pr.columns if c not in('site_id','y_true')]
acc=pd.DataFrame({m:pr.groupby('site_id').apply(lambda x:(x[m]==x['y_true']).mean()) for m in models})
print('\nper-site accuracy (rows = held-out site-year):'); print(acc.round(3).to_string())
print('\nmean rank (1 = best):'); print(acc.rank(axis=1,ascending=False).mean().sort_values().round(2).to_string())
st,pv=friedmanchisquare(*[acc[m] for m in models]); print(f'\nFriedman chi2={st:.2f}, p={pv:.4f}')
