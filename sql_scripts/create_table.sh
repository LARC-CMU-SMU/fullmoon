#!/bin/bash
set -e
#make sure the env variables POSTGRES_DB, POSTGRES_USER are set

#create the schema
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
	\connect $POSTGRES_DB;
	CREATE SCHEMA $POSTGRES_SCHEMA;
EOSQL


#execute sql files in current directory
echo $(ls)
for f in /docker-entrypoint-initdb.d/sql/*.sql; do
    echo "Executing $f"
    psql -v --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" -w -f "$f"
    psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
	COMMIT;
EOSQL
done

