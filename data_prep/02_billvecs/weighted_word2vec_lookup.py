'''
Use bill vector pairwise distances
to lookup a bill's closest relatives.
'''

import pandas as pd
from pprint import pprint

dfm = pd.read_csv('../data/bill_metadata_andrew.csv')
dfm = dfm[['bill_id','official_title']]
dfm = dfm.set_index('bill_id')

dfd = pd.read_csv('../data/bill_document_distances.csv')

print(dfd.head(3))
dfd = dfd.set_index('bill_id_1')
df = dfd.join(dfm)
print(df.head(3))
df = df.rename(columns={'official_title':'official_title_1'})
df = df.reset_index()
df = df.rename(columns={'index':'bill_id_1'})
df = df.set_index('bill_id_2')
df = df.join(dfm)
df = df.rename(columns={'official_title':'official_title_2'})
df = df.reset_index()
df = df.rename(columns={'index':'bill_id_2'})
print(df.head(3))

tag = 'hr3184-114'
pprint(df[df['bill_id_1']==tag].head(5).to_dict(orient='records'))

