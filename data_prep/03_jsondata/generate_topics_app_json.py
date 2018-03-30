'''
Pull data together from Postgres 
and load into a single JSON file
that is used by the topics web app.

Modified from Mattie's createFamiliesFast.py
'''

import os
import sqlalchemy
import requests
import re
import pandas as pd
import json


def text_url(bill_id):
    r = re.search('([a-z]{1,5})([0-9]{1,8})-([0-9]{1,5})', bill_id, re.IGNORECASE)
    billtype,num,congress=r.groups(0)
    return 'https://www.govinfo.gov/link/bills/%s/%s/%s' % (congress,billtype,num)

# e.g. https://www.congress.gov/bill/115th-congress/house-bill/195
def web_url(bill_id):
    r = re.search('([a-z]{1,5})([0-9]{1,8})-([0-9]{1,5})', bill_id, re.IGNORECASE)
    billtype,num,congress=r.groups(0)
    full_type = {'hr':'house-bill','s':'senate-bill'}
    return 'https://www.congress.gov/bill/%sth-congress/%s/%s' % (congress,full_type[billtype],num)

def bill_id_nice(bill_id):
    r = re.search('([a-z]{1,5})([0-9]{1,8})-([0-9]{1,5})', bill_id, re.IGNORECASE)
    billtype,num,congress=r.groups(0)
    nice_type = {'hr':'H.R.','s':'S.'}
    return nice_type[billtype]+''+num


def build_bills(engine,params):

    query = '''
        SELECT meta.*,sim.similar_bill_ids,sim.similar_bill_cosines FROM
        (
            -- Bill metadata,
            -- plus social tags
            -- and legislator metadata.
            select x.bill_id,
            x.number,
            x.congress,
            x.chamber,
            x.introduced_at,
            x.short_title, 
            x.official_title, 
            x.popular_title,
            x.status, 
            x.status_at,
            x.house_passage_result,
            x.senate_passage_result,
            x.sponsor_name,
            x.sponsor_title,
            x.sponsor_state,
            x.sponsor_bioguide_id,
            leg.party as sponsor_party,
            leg.gender as sponsor_gender,
            x.policy_area,
            spa.super_policy_area,
            array_agg(y.social_tag) as social,
            array_agg(y.cosine) as cos
            from bill_metadata as x
            join social_tags_bills_similarity as y
            on x.bill_id=y.bill_id
            left join super_policy_areas as spa
            on x.policy_area=spa.policy_area
            left join legislators_current as leg
            on x.sponsor_bioguide_id=leg.bioguide_id
            group by x.bill_id, 
            x.number,
            x.congress,
            x.chamber,
            x.introduced_at,
            x.short_title, 
            x.official_title, 
            x.popular_title,
            x.status, 
            x.status_at,
            x.house_passage_result,
            x.senate_passage_result,
            x.sponsor_name,
            x.sponsor_title,
            x.sponsor_state,
            x.sponsor_bioguide_id,
            sponsor_party,
            sponsor_gender,
            x.policy_area,
            spa.super_policy_area
        ) meta
        LEFT OUTER JOIN
        (
            -- For each bill, get an array of other bill ids
            -- that have small cosine distance between
            -- the bill document vectors.
            SELECT
            x.bill_id_1 as bill_id, 
            array_agg(x.bill_id_2) as similar_bill_ids,
            array_agg(x.cosine) as similar_bill_cosines
            FROM bill_document_distances AS x
            JOIN bill_metadata AS y 
            ON x.bill_id_1=y.bill_id 
            JOIN bill_metadata AS z 
            ON x.bill_id_2=z.bill_id 
            WHERE x.cosine < 0.05
            AND x.bill_id_1 != x.bill_id_2
            GROUP BY x.bill_id_1
        ) sim
        ON (meta.bill_id = sim.bill_id)
        '''

    with engine.connect() as conn:
        df = pd.read_sql(query, conn,params=params)

    df['text_url'] = df['bill_id'].apply(text_url)
    df['web_url'] = df['bill_id'].apply(web_url)
    df['bill_id_nice'] = df['bill_id'].apply(bill_id_nice)

    # JSON cannot serialize date objects
    df['introduced_at'] = df['introduced_at'].apply(str)
    df['status_at'] = df['status_at'].apply(str)
    # Store cosines as numeric types
    df['cos'] = df['cos'].apply(lambda i: [float(j) for j in i if j is not None])

    # Combine topics into object for JSON
    df['topics'] = df[['social','cos']].apply(lambda x: {'tags':[{'name':n,'cosine':c} for n,c in zip(x[0],x[1])]},axis=1)

    # Combine similar bills into object for JSON
    def roll_up_similar(x):
        # some bills have no similar bills
        if len(x)==0 or x[0] is None or x[1] is None:
            return {'bills':[]}
        return {'bills':[{'bill_id':n,'cosine':c} for n,c in zip(x[0],x[1])]}
    df['similar_bills'] = df[['similar_bill_ids','similar_bill_cosines']].apply(roll_up_similar,axis=1)

    #####################################################################
    # Up to here, we have grabbed bills across *all dates*. 
    # Including *all* bills makes the JSON file too large (~16MB). 
    # Here, we remove the bills that are:
    #   (i) not within the desired date range
    #   (ii) not similar to bills within the desired date range.
    #####################################################################
    timelinedf = df.copy()
    timelinedf = timelinedf[(timelinedf['introduced_at'] > params['mindate']) & (timelinedf['introduced_at'] < params['maxdate'])]
    
    # The ids that are in the timeline itself
    ids_in_timeline = timelinedf['bill_id'].values.tolist()
    print('%d ids in timeline.' % (len(ids_in_timeline)))
    
    # The ids of bills that are referenced in the similar ids of the timeline bills.
    ids_referenced_in_timeline = timelinedf['similar_bill_ids'].values.tolist()
    # This is a list of lists. Flatten it.
    flat_ids = []
    for sub in [x for x in ids_referenced_in_timeline if x is not None]:
        flat_ids.extend(sub)
    unique_ids_referenced_in_timeline = list(set(flat_ids))
    print('%d ids referenced by timeline.' % (len(unique_ids_referenced_in_timeline)))

    # Keep all bills that are in timeline or referenced by timeline
    ids_to_keep = ids_in_timeline + unique_ids_referenced_in_timeline
    print('Keeping %d ids.' % (len(ids_to_keep)))

    # target = 'hr5643-114'
    # print(target)
    # print(target in ids_to_keep)
    # print(target in ids_in_timeline)
    # print(target in flat_ids)
    # print(target in unique_ids_referenced_in_timeline)
    
    # Keep only these bills
    df = df[df['bill_id'].isin(ids_to_keep)]

    # TODO
    # Why is DF still missing ids??
    print(len(df))
    print(len(df)==len(ids_to_keep))

    #####################################################################

    return df

def build_timeline(engine,billdf,params):
    timeline = []

    # No guarantee that bill metadata is restricted to the same
    # date range that we want for the timeline. Restrict timeline here.
    df = billdf.copy()
    df = df[(df['introduced_at'] > params['mindate']) & (df['introduced_at'] < params['maxdate'])]

    # Apply requirements on timeline quality
    # df = df[df['cos'] <= params['max_tag_cosine']]
    # df = df[df['']]

    for date in df['introduced_at'].unique():
        currDate = {'datetime': date, 'bills': df.loc[df['introduced_at'] == date, 'bill_id'].values.tolist()}
        timeline.append(currDate)

    return timeline


if __name__ == '__main__':

    # Connect to local PostgreSQL
    user = 'ubuntu'
    password = ''
    dbname = 'congress'
    host = 'localhost'
    local_port = '5432'
    es = "postgresql+psycopg2://"+user+":"+password+"@/"+dbname+"?host="+host+"&port="+local_port
    engine = sqlalchemy.create_engine(es)
    print(engine)

    params = {
        'mindate':'2017-11-01',
        'maxdate':'2018-02-01',
        'max_tag_length':30,
        'max_tag_cosine':0.3
    }

    billdf = build_bills(engine,params)
    timeline = build_timeline(engine,billdf,params)

    # remove columns that we do not need to send in JSON
    del billdf['cos']
    del billdf['social']
    del billdf['similar_bill_ids']
    del billdf['similar_bill_cosines']
    bills = billdf.set_index('bill_id').to_dict(orient='index')
    overallJSON = {"timeline": timeline, "bills": bills}

    outpath = '/home/ubuntu/app/www/static/data/topics_data_feb092018.json'
    print('Writing to %s' % (outpath))
    with open(outpath,'w') as f:
        json.dump(overallJSON,f)
