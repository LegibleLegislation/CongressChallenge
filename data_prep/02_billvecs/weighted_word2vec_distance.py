'''
Use bill vectors to calculate and store
pairwise distances between bills.
'''

import pandas as pd
from pprint import pprint
import scipy.spatial.distance
from joblib import Parallel, delayed

def pairwise_distances(i, vector_list, u, threshold = 0.1):
    '''
    Given a vector (u) list of vectors (each v), compute
    the cosine angle ("distance") and, if is less than 
    the threshold, store it in a dictionary.
    The dictionary has keys that correspond to the order
    of the input vector_list.
    '''
    distances = {}
    for indx,v in enumerate(vector_list):
        distance = scipy.spatial.distance.cosine(u,v)
        if distance < threshold:
            distances[indx] = distance
    return {i:distances}


words_column = 'official_title'
tag_column = 'bill_id'
dfm = pd.read_csv('../data/bill_metadata_andrew.csv')
dfm = dfm[[tag_column,words_column,'short_title']]
dfv = pd.read_csv('../data/bill_document_vectors.csv',header=None,index_col=None)

indexes = dfm.index.tolist()
vectors = dfv.values.tolist()
combined = list(zip(indexes,vectors))

list_of_distances = [pairwise_distances(i,vectors,u) for i,u in combined]
# list_of_distances = Parallel(n_jobs=2, verbose=5, backend='threading')(delayed(pairwise_distances)(i,vectors,u) for i,u in combined)

# convert list of dictionaries into a form
# that Pandas can turn into a dataframe.
doubledict = {}
for ddict in list_of_distances:
    # Each item in the list is set up like:
    # {1: {1: 0.0, 8085: 0.09823015777941912, 21561: 0.09823015777941912, 23573: 0.08471914669921032}}
    # There is a single key for the outer dict (bill_1).
    bill_1 = list(ddict.keys())[0]
    distances = ddict[bill_1]
    for bill_2, cosine in distances.items():
        doubledict[(bill_1,bill_2)] = cosine

# create a dataframe of bill distances (bill_1,bill_2,cosine between 1 and 2)
ddf = pd.DataFrame.from_dict(doubledict,orient='index')
ddf = ddf.reset_index()
ddf = ddf.rename(columns={0:'cosine'})
ddf['bill_1'] = ddf['index'].apply(lambda x: x[0])
ddf['bill_2'] = ddf['index'].apply(lambda x: x[1])
ddf = ddf[['bill_1','bill_2','cosine']]
ddf = ddf[ddf['bill_1']!=ddf['bill_2']] # drop rows where bill is compared to itself
ddf = ddf.set_index('bill_1')

# join with metadata to get bill_ids (e.g. 'hr3184-114')
# instead of integers
df = ddf.join(dfm[['bill_id']])
df = df.rename(columns={'bill_id':'bill_id_1'})
df = df.reset_index().set_index('bill_2')
df = df.join(dfm[['bill_id']])
df = df.rename(columns={'bill_id':'bill_id_2'})
df = df[['bill_id_1','bill_id_2','cosine']]
df = df.sort_values(by=['bill_id_1','bill_id_2','cosine'],ascending=[True,True,True])

df.to_csv('../data/bill_document_distances.csv',header=True,index=False)
