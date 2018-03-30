
'''
'''

import spacy
import numpy as np
import pandas as pd
from pprint import pprint
import scipy.spatial.distance
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
import json
import re
import os

def normal(token):
    # Should the token be kept? (=is normal)
    # Spacy treats 'To' (title case) as *not a stop word*, but
    # gensim will not compute tf-idf for 'To'. To remove 'To' as a stop word here, I 
    # do an extra test to see if the lower case token is a stop word.
    return not token.is_stop and not token.is_punct and not nlp.vocab[token.lower_].is_stop

def tokenizer(input_string):
    doc = nlp(input_string)
    tokens = [token for token in doc if normal(token)]
    return tokens

def lemmatizer(tokens):
    lemmas = [t.lemma_ for t in tokens]
    return lemmas

def vectorizer(tokens):
    vectors = [t.vector for t in tokens]
    return vectors

nlp = spacy.load('en_core_web_md', entity = False, parser = False)


# Connect to local PostgreSQL
user = 'ubuntu'
password = ''
dbname = 'congress'
host = 'localhost'
local_port = '5432'
es = "postgresql+psycopg2://"+user+":"+password+"@/"+dbname+"?host="+host+"&port="+local_port
engine = sqlalchemy.create_engine(es)
print(engine)

Session = sessionmaker(bind=engine)
session = Session()
print('Session created')

socialTagVectors = pd.read_csv('socialTagVectors.csv')
congressRareTags = session.execute("SELECT bill_id, social_tags FROM congress_tagging;")#pd.read_csv('congress_rare_tags.csv', header = 0)
congressRareTags = congressRareTags.fetchall()
congressbillid = [i[0] for i in congressRareTags]
congresstag = [i[1] for i in congressRareTags]

congressRareTags = pd.DataFrame({'bill_id': congressbillid, 'social_tags': congresstag})
billVectors = pd.read_csv('bill_document_vectors.csv')

print('read 3')

words_column = 'official_title'
tag_column = 'bill_id'
dfm = pd.read_csv('bill_metadata_andrew.csv')
dfm = dfm[['bill_id',words_column,'short_title']]
dfv = pd.read_csv('bill_document_vectors.csv',header=None,index_col=None)

bill_ids = dfm.bill_id.values.tolist()
vectors = dfv.values.tolist()

df = pd.DataFrame({'bill_id':bill_ids,'vector':vectors})

socialTagOrder = pd.read_csv('socialTagOrder.csv', encoding = 'cp1252')

socialtagsorder = socialTagOrder.values.tolist()
socialvectors = socialTagVectors.values.tolist()

socialtagsorder = [i[0] for i in socialtagsorder]

socialTagOrder = pd.DataFrame({'social_tag': socialtagsorder, 'vector': socialvectors})

cosineSimilarity = {'bill_id': [], 'social_tag': [], 'cosine': []}

failedOn = []

print('read all')
count = 0
for i in bill_ids:
    #get social tags
    print(count)
    count += 1

    social = list(congressRareTags.loc[congressRareTags['bill_id'] == i, 'social_tags'])

    for j in social:

        u = socialTagOrder.loc[socialTagOrder['social_tag'] == j, 'vector'].values.tolist()
        v = df.loc[df['bill_id'] == i, 'vector'].values.tolist()
        try:
            cosine = scipy.spatial.distance.cosine(u,v)

            cosineSimilarity['bill_id'].append(i)
            cosineSimilarity['social_tag'].append(j)
            cosineSimilarity['cosine'].append(cosine)
        
        except:
            failedOn.append([i, j])
        
finaldf = pd.DataFrame(cosineSimilarity)

finaldf.to_csv('SocialTagsBillsSimilarity.csv', index = None)

