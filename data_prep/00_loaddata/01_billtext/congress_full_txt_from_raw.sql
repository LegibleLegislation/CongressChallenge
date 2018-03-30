-- Extract full text table from raw txt data (loaded from congress-master files)
-- Run as: 
--  time psql congress -f congress_full_txt_from_raw.sql

DROP TABLE IF EXISTS congress_full_txt;

CREATE TABLE congress_full_txt AS
(
    SELECT
        data_id,
        (regexp_matches(path,'home/ubuntu/andrew/congress-master/data/([0-9]{1,4})'))[1] as congress,
        (regexp_matches(path,'home/ubuntu/andrew/congress-master/data/[0-9]{1,4}/bills/([a-z]{1,15})/'))[1] as bill_type,
        (regexp_matches(path,'home/ubuntu/andrew/congress-master/data/[0-9]{1,4}/bills/[a-z]{1,15}/([a-z0-9]{1,15})/'))[1] as bill_number,
        (regexp_matches(path,'home/ubuntu/andrew/congress-master/data/[0-9]{1,4}/bills/[a-z]{1,15}/[a-z0-9]{1,15}/text-versions/([a-z]{1,15})'))[1] as status_code,
        data
    FROM congress_full_raw_txt
);

ALTER TABLE congress_full_txt ADD COLUMN bill_id TEXT;

UPDATE congress_full_txt SET bill_id = bill_number || '-' || congress;

SELECT data_id,congress,bill_type,bill_number,status_code,bill_id FROM congress_full_txt LIMIT 10;
