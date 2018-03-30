'''
Calculate and store "bill vectors"
by weighting word vectors by bill tf-idf.
'''

import gensim, re
from pprint import pprint
import spacy
import numpy as np

from sshtunnel import SSHTunnelForwarder
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

fw = SSHTunnelForwarder(('18.218.108.55', 22),
    ssh_private_key="/Users/U6035044/keys/mitexterns2018.pem",
    ssh_username="ubuntu",
    remote_bind_address=('localhost', 5432))

with fw as server:

    server.start()
    print('SSH session created')

    user = 'ubuntu'
    password = ''
    dbname = 'congress'
    host = 'localhost'
    local_port = str(server.local_bind_port)
    es = "postgresql+psycopg2://"+user+":"+password+"@/"+dbname+"?host="+host+"&port="+local_port
    engine = create_engine(es)
    print(engine)

    Session = sessionmaker(bind=engine)
    session = Session()
    print('Session created')

    query = "SELECT data_id,bill_id,official_title FROM bill_metadata_andrew"
    dfm = pd.read_sql(query,engine)



# Note: Default word vector set only uses 5000 words.
# User should download full set. See here:
# https://github.com/explosion/spaCy/issues/1117
nlp = spacy.load('en',entity=False,parser=False)

words_column = 'official_title'
tag_column = 'bill_id'

print('Reading bill metadata')
# dfm = pd.read_csv('../data/bill_metadata_andrew.csv')
print(dfm.shape)

stop_words = nlp.Defaults.stop_words

def normal(token):
    # Should the token be kept? (=is normal)
    return not token.is_stop and not token.is_punct \
        and not token.lower_ in stop_words \
        and not token.lemma_ in stop_words

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


dfm = dfm[[tag_column,words_column]]
print('Tokenizing/lemmatizing')
dfm['tokens'] = dfm[words_column].apply(tokenizer)
dfm['words'] = dfm['tokens'].apply(lambda x: [str(y).lower() for y in x])
# dfm['words'] = dfm['tokens'].apply(lemmatizer)
dfm['vectors'] = dfm['tokens'].apply(vectorizer)

data = dfm[[tag_column,'words','vectors']]
data = data.rename(columns={tag_column:'tag'})
pprint(data.head(3))


# TF-IDF WEIGHTS
print('TF-IDF')
texts = data['words'].values.tolist()
dictionary = gensim.corpora.Dictionary(texts)
corpus = [dictionary.doc2bow(text) for text in texts]
tfidf_model = gensim.models.tfidfmodel.TfidfModel(dictionary=dictionary)
tfidf_dict = {dictionary.get(id): value for doc in tfidf_model[corpus] for id, value in doc}
tfidf_df = pd.DataFrame.from_dict(tfidf_dict,orient='index')
tfidf_df = tfidf_df.rename(columns={0:'weight'})
pprint(tfidf_df.head(10))

print('Number of tokens = %d' % (len(tfidf_df)))

row = tfidf_df.sort_values(by='weight',ascending=False).head(1)
print('Max weighted token = %s (weight = %f)' % (row.index,row['weight']))

row = tfidf_df.sort_values(by='weight',ascending=True).head(1)
print('Min weighted token = %s (weight = %f)' % (row.index,row['weight']))

# Sum vectors
print('Creating document vectors from word vectors.')
weighted_vectors_row = []
for indx,row in data.iterrows():

    new_vectors = []
    for word,vector in zip(row['words'],row['vectors']):
        
        weight = tfidf_df.loc[word]['weight']
        new_vector = weight * vector
        new_vectors.append(new_vector)

    weighted_vectors_row.append(new_vectors)

data['weighted_vectors'] = weighted_vectors_row
data['document_vectors'] = data['weighted_vectors'].apply(lambda x: np.sum(x,axis=0))
pprint(data.head(3))

# Write vectors to disk
matrix = np.vstack(data['document_vectors'].values.tolist())
print(matrix[0:3,0:3])
outdata = pd.DataFrame(matrix)
outdata.to_csv('../data/bill_document_vectors.csv',header=False,index=False)
