
import json
import sqlalchemy
import requests
import os


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
IN_TABLE = 'congress_intelligent_tags_test'
OUT_TABLE = 'congress_tagging_test'
LIMIT = 1
OFFSET = 0

with engine.connect() as conn:

    rows = conn.execute("SELECT data_id,bill_id,data::jsonb FROM {0} LIMIT {1} OFFSET {2};".format(IN_TABLE,LIMIT,OFFSET))
    print(rows.keys())

    query = '''DROP TABLE IF EXISTS {0}'''.format(OUT_TABLE)
    print(query)
    conn.execute(query)

    query = '''CREATE TABLE {0}
    (bill_id TEXT,
    social_tags TEXT,
    relevance INT);
    '''.format(OUT_TABLE)
    print(query)
    conn.execute(query)

    for row in rows:
        
        first = row[1]
        for t in list(row[2]):

            if 'SocialTag' in t:

                name = row[2][t][u'name']
                name = name.replace("'", '')
                query = '''INSERT INTO 
                {0} (bill_id, social_tags, relevance) 
                VALUES 
                ('{1}', '{2}','{3}');'''.format(OUT_TABLE,str(first),name,str(row[2][t][u'importance']))
                print(query) # NOTE toggle for debugging
                try:
                    conn.execute(query)
                except:
                    print(query)
                    raise