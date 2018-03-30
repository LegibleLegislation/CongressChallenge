-- Extract metadata from raw JSON table.
-- Run as: 
--  time psql congress -f metadata_from_json.sql

DROP TABLE IF EXISTS bill_metadata;

CREATE TABLE bill_metadata AS
(
    SELECT
        data_id,
        data->>'bill_id' as bill_id,
        cast(data->>'number' as int) as number,
        cast(data->>'introduced_at' as date) as introduced_at,
        cast(data->>'congress' as int) as congress,
        data->>'chamber' as chamber,
        data->>'official_title' as official_title,
        data->>'short_title' as short_title,
        data->>'popular_title' as popular_title,
        data->'summary'->>'text' as summary,
        data->>'status' as status,
        cast(data->>'status_at' as date) as status_at,
        data->'history'->>'house_passage_result' as house_passage_result,
        data->'history'->>'senate_passage_result' as senate_passage_result,
        data->'sponsor'->>'name' as sponsor_name,
        data->'sponsor'->>'title' as sponsor_title,
        data->'sponsor'->>'state' as sponsor_state,
        data->'sponsor'->>'bioguide_id' as sponsor_bioguide_id,
        data->>'subjects_top_term' as policy_area,
        data->>'subjects' as subjects
    FROM congress_data_json
);


-- DROP TABLE IF EXISTS bill_subjects;

-- CREATE TABLE bill_subjects AS
-- (
--     SELECT
--         data_id,
--         data->>'bill_id' as bill_id,
--         jsonb_array_elements_text(data->'subjects') as subject
--     FROM congress_data_json
--     WHERE path LIKE '%/bills/hr/%'
--     OR path LIKE '%/bills/s/%'
-- );