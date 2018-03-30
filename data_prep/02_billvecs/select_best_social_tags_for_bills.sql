
DROP TABLE IF EXISTS social_tags_bills_similarity;
CREATE TABLE IF NOT EXISTS social_tags_bills_similarity (
bill_id TEXT,
cosine NUMERIC,
social_tag TEXT
);
COPY social_tags_bills_similarity FROM '/home/ubuntu/SocialTagsBillsSimilarity2.csv' DELIMITER ',' CSV HEADER ENCODING 'LATIN1';


-- -- NEW BIG QUERY, FEB 9 2018
-- -- FOR TOPICS APP.
-- SELECT meta.*,sim.similar_bill_ids,sim.similar_bill_cosines FROM
-- (
--     -- Bill metadata,
--     -- plus social tags
--     -- and legislator metadata.
--     select x.bill_id,
--     x.number,
--     x.congress,
--     x.chamber,
--     x.introduced_at,
--     x.short_title, 
--     x.official_title, 
--     x.popular_title,
--     x.status, 
--     x.status_at,
--     x.house_passage_result,
--     x.senate_passage_result,
--     x.sponsor_name,
--     x.sponsor_title,
--     x.sponsor_state,
--     x.sponsor_bioguide_id,
--     leg.party as sponsor_party,
--     leg.gender as sponsor_gender,
--     x.policy_area,
--     spa.super_policy_area,
--     array_agg(y.social_tag) as social,
--     array_agg(y.cosine) as cos
--     from bill_metadata as x
--     join social_tags_bills_similarity as y
--     on x.bill_id=y.bill_id
--     left join super_policy_areas as spa
--     on x.policy_area=spa.policy_area
--     left join legislators_current as leg
--     on x.sponsor_bioguide_id=leg.bioguide_id
--     group by x.bill_id, 
--     x.number,
--     x.congress,
--     x.chamber,
--     x.introduced_at,
--     x.short_title, 
--     x.official_title, 
--     x.popular_title,
--     x.status, 
--     x.status_at,
--     x.house_passage_result,
--     x.senate_passage_result,
--     x.sponsor_name,
--     x.sponsor_title,
--     x.sponsor_state,
--     x.sponsor_bioguide_id,
--     sponsor_party,
--     sponsor_gender,
--     x.policy_area,
--     spa.super_policy_area
-- ) meta
-- LEFT OUTER JOIN
-- (
--     -- For each bill, get an array of other bill ids
--     -- that have small cosine distance between
--     -- the bill document vectors.
--     SELECT
--     x.bill_id_1 as bill_id, 
--     array_agg(x.bill_id_2) as similar_bill_ids,
--     array_agg(x.cosine) as similar_bill_cosines
--     FROM bill_document_distances AS x
--     JOIN bill_metadata AS y 
--     ON x.bill_id_1=y.bill_id 
--     JOIN bill_metadata AS z 
--     ON x.bill_id_2=z.bill_id 
--     WHERE x.cosine < 0.05
--     AND x.bill_id_1 != x.bill_id_2
--     GROUP BY x.bill_id_1
-- ) sim
-- ON (meta.bill_id = sim.bill_id)