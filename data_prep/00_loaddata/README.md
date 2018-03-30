#Legible Legislation

First the user must download the bill data from FDSys using the public domain 'congress' tools:

https://github.com/unitedstates/congress/wiki/bills
https://github.com/unitedstates/congress/wiki/bill-text

Example:

./run fdsys --collections=BILLSTATUS
./run bills 
./run fdsys --collections=BILLS --congress=112 --store=text --bulkdata=False

Use this repo's load_json_into_postgres.py tool to load the data into PostgreSQL on the local machine.

Use this repo's metadata_from_json.sql to build a clean table of bill data.

Analogous tools are available to load the full bill text into a clean table.


