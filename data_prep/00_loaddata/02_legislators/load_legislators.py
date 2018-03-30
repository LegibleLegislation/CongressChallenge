'''
Download members of congress data, load into Postgres.
'''

import os
import sqlalchemy
import requests

# from Zac, July 20 2017
# fix slow pandas to_sql method with monkey patch
from pandas.io.sql import SQLTable
def _execute_insert(self, conn, keys, data_iter):
    print("Using monkey-patched _execute_insert")
    data = [dict((k, v) for k, v in zip(keys, row)) for row in data_iter]
    conn.execute(self.insert_statement().values(data))
SQLTable._execute_insert = _execute_insert
import pandas as pd

# Available in the public domain from github.com/unitedstates:
# https://github.com/unitedstates/congress-legislators

data_sets = [
    {'table':'legislators_current',
    'url':'https://theunitedstates.io/congress-legislators/legislators-current.csv'},
    {'table':'legislators_historical',
    'url':'https://theunitedstates.io/congress-legislators/legislators-historical.csv'},
]

for data_set in data_sets:

    url = data_set['url']

    print('Downloading %s' % (url))
    df = pd.read_csv(url)

    # Connect to local PostgreSQL
    user = 'ubuntu'
    password = ''
    dbname = 'congress'
    host = 'localhost'
    local_port = '5432'
    es = "postgresql+psycopg2://"+user+":"+password+"@/"+dbname+"?host="+host+"&port="+local_port
    engine = sqlalchemy.create_engine(es)
    print(engine)

    with engine.connect() as conn:

        table = data_set['table']

        query = '''
        -- also drop view that combines legislator tables
        DROP TABLE %s CASCADE;
        ''' % (table)
        print(query)
        conn.execute(query)

        df.to_sql(table,conn,if_exists='replace',index=False)

        query = '''
        ALTER TABLE %s
        ALTER COLUMN birthday TYPE date USING birthday::date,
        ALTER COLUMN district TYPE int,
        ALTER COLUMN thomas_id TYPE int,
        ALTER COLUMN cspan_id TYPE int,
        ALTER COLUMN votesmart_id TYPE int,
        ALTER COLUMN washington_post_id TYPE int,
        ALTER COLUMN icpsr_id TYPE int,
        ALTER COLUMN twitter TYPE text,
        ALTER COLUMN facebook TYPE text,
        ALTER COLUMN youtube TYPE text,
        ALTER COLUMN youtube_id TYPE text;
        ''' % (table)
        print(query)
        conn.execute(query)


# Combine all legislator tables 
# (e.g. current and historical people)
with engine.connect() as conn:

    subq = ['select * from '+str(d['table']) for d in data_sets]
    union = ' union '.join(subq)

    query = '''
    CREATE VIEW legislators AS
    (%s);
    ''' % (union)
    print(query)
    conn.execute(query)

