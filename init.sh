#! /bin/bash

echo "start creating folders..."
mkdir -p docker_mount/logs
echo "logs ...done."
mkdir -p docker_mount/data/postgre/db
echo "data/postgre/db ...done."
mkdir -p docker_mount/data/postgre/scripts
echo "data/postgre/scripts ...done."
cp -r sql_scripts/* docker_mount/data/postgre/scripts/
echo "copying sql scripts to postgre scripts ...done"
mkdir -p docker_mount/data/app
echo "data/app ...done."

