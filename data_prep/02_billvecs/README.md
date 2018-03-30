#Legible Legislation

Compute the document vectors (embeddings) for bills using weighted_word2vec.py. This code uses Spacy's pre-trained word embeddings.
https://spacy.io/

You may need to download the embeddings after installing spacy:
python -m spacy download en_core_web_md

Find the pairwise bill distances with weighted_word2vec_distance.py, and the cosine similarity to tags with findCosine.py. Finally, use select_best_social_tags_for_bills.sql to create the PostgreSQL table of the best tags (smallest vector cosine distance to the associated bill).


