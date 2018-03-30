'''
Load nested JSON data files on disk into PostgreSQL table.
'''

import json
import os
import sqlalchemy


def main():

    data_dir = '/home/ubuntu/data'

    user = 'ubuntu'
    password = ''
    dbname = 'congress'
    host = 'localhost'
    local_port = '5432'

    es = "postgresql+psycopg2://"+user+":"+password+"@/"+dbname+"?host="+host+"&port="+local_port
    engine = sqlalchemy.create_engine(es)
    print(engine)

    table = 'congress_data_json'
    print(table)

    load(data_dir,engine,table)

def load(data_dir,engine,table):

    with engine.connect() as conn:

        query = '''DROP TABLE IF EXISTS %s''' % (table)
        print(query)
        conn.execute(query)

        query = '''CREATE TABLE %s 
        (data_id SERIAL NOT NULL PRIMARY KEY,
        path TEXT,
        data JSONB)
        ''' % (table)
        print(query)
        conn.execute(query)

        for indx, (root, dirs, files) in enumerate(os.walk(os.path.expanduser(data_dir))):
            for f in files:

                fname = os.path.join(root, f)
                if fname.endswith("data.json"):

                    data = json.load(open(fname))
                    data_str = json.dumps(data)
                    escaped_data_str = data_str.replace('%','%%')

                    query = '''INSERT INTO %s 
                    (path,data)
                    VALUES
                    ('%s',$$%s$$)
                    ''' % (table,fname,escaped_data_str)
                    # print(query)
                    try:
                        conn.execute(query)
                    except:
                        print(query)
                        raise

                    if indx % 500 == 0:
                        print('Completed %d.' % indx)

        query = '''select count(*) from %s;''' % (table)
        print(query)
        result = conn.execute(query)
        print('Rows in table: %d' % (result.fetchone()[0]))
        

        query = '''select count(*) from (select path from %s group by path) x;''' % (table)
        print(query)
        result = conn.execute(query)
        print('Unique path rows in table: %d' % (result.fetchone()[0]))


if __name__ == '__main__':
    main()
