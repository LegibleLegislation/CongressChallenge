
import json
import sqlalchemy
import requests
import os

# from Zac, July 20 2017
# fix slow pandas to_sql method with monkey patch
from pandas.io.sql import SQLTable
def _execute_insert(self, conn, keys, data_iter):
    print("Using monkey-patched _execute_insert")
    data = [dict((k, v) for k, v in zip(keys, row)) for row in data_iter]
    conn.execute(self.insert_statement().values(data))
SQLTable._execute_insert = _execute_insert
import pandas as pd

# Connect to local PostgreSQL
user = 'ubuntu'
password = ''
dbname = 'congress'
host = 'localhost'
local_port = '5432'
es = "postgresql+psycopg2://"+user+":"+password+"@/"+dbname+"?host="+host+"&port="+local_port
engine = sqlalchemy.create_engine(es)
print(engine)

# NOTE: CHANGE THESE PARAMETERS 
# AFTER TESTING.
OUT_TABLE = 'congress_intelligent_tags_test'
LIMIT = 1
OFFSET = 0

query = '''
CREATE TABLE %s (
    data_id SERIAL NOT NULL PRIMARY KEY,
    bill_id TEXT,
    -- data stores JSONB, but because Pandas to_sql
    -- cannot write JSONB, I use text.
    data TEXT    
);
''' % (OUT_TABLE)
print(query)
engine.execute(query)
    
query = '''SELECT bill_id,summary as data 
FROM bill_metadata 
where bill_id is not null 
LIMIT {0} OFFSET {1};'''.format(LIMIT,OFFSET)

df_summaries = pd.read_sql(query,engine)

out_data = {'bill_id':[],'data':[]}
for indx,row in df_summaries.iterrows():
    
    text = row['data']
    msg = text.encode('utf-8')

    token = os.environ.get('TRIT_TOKEN')
    
    url = 'https://api.thomsonreuters.com/permid/calais'
    headers = {'X-AG-Access-Token':token,
        'Content-Type':'text/raw',
        'outputformat':'application/json'}
    r = requests.post(url,data=msg,headers=headers)
    print(row['bill_id'],r) # should be 200
    j = r.json()

    # For debugging:
    # social_tags = [attrs for _,attrs in j.items() if '_typeGroup' in attrs and attrs['_typeGroup'] == 'socialTag']
    # names = [st['name'] for st in social_tags]
    # scores = [st['importance'] for st in social_tags]
    # print(row['bill_id'], list(zip(names,scores)))

    out_data['bill_id'].append(row['bill_id'])
    out_data['data'].append(json.dumps(j)) # to_sql cannot write JSON, use TEXT instead

df_tags = pd.DataFrame(data=out_data)
print(df_tags.head(3))

df_tags.to_sql(OUT_TABLE,engine,if_exists='append',index=False)
