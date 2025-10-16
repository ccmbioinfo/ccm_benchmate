#!/bin/bash

set -oe pipefail

show_usage(){
  echo "Install Benchmate"
  echo "-p install postgres with pgvector"
  echo "-d postgres location default current directory"
  echo "-c create database"
  echo "-e .env file that contains the database name, port, username and password see .env for an example"
  exit 1
}

while getopts 'e:d:cph' flag; do
  case "${flag}" in
    e) env_file="${OPTARG}" ;;
    d) database_dir="${OPTARG}" ;;
    c) create_database='true' ;;
    p) install_postgres='true';;
    h) show_usage='true';;
  esac
done

if [[ $show_usage == "true" ]];then
  show_usage
fi

# install conda if it's not installed
if command -v conda > /dev/null 2>&1;
 then
  echo "Conda is installed will continue with env creation."
else
  echo "Conda is not installed will install miniconda now."
    mkdir -p ~/miniconda3
    wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O ~/miniconda3/miniconda.sh
    bash ~/miniconda3/miniconda.sh -b -u -p ~/miniconda3
    rm ~/miniconda3/miniconda.sh
fi

echo "creating environment"
conda env create -f environment.yaml
conda activate benchmate

if [[ $install_postgres == 'true' ]];
echo "installing postgres"
then
  conda install postgresql=17 git make gcc=14 gxx=14
  # install pgvector
  echo "installing pg vector"
  git clone https://github.com/pgvector/pgvector.git
  cd pgvector
  make
  make install
  cd ../
  rm -rf pgvector
fi

if [[ $create_database == 'true' ]];
echo "creating database"
then
  if [[ $database_dir == "" ]];
  echo "no database directory specified using the current directory $pwd"
  then
    database_dir=$(pwd -P)
  fi
  # export .env variables if they do not conform to the example that's on you
  if [ -f "$env_file" ];
  then
    while read -r line
    do
      export $line
    done < $env_file
  else
    echo "No env file specified, cannot create the database without that information"
    exit 1
  fi
  echo "creating database $PG_DATABASE for $PG_USER"
  mkdir -p $database_dir/db_data
  initdb -D $database_dir/db_data
  #TODO need to check port if it's not 5432 then I will need to do other things
  if [[ $PG_PORT != 5432 ]];
  then
    echo "a different port has been specified other than the default editing postgresql.conf file"
    sed -i.bak "s/^#* *port *= *[0-9]*/port = ${PG_PORT}/" "${database_dir}/db_data/postgresql.conf"
  fi
  pg_ctl -D $database_dir/db_data -l $database_dir/logfile start
  psql -v ON_ERROR_STOP=1 --port "${PG_PORT}" -d template1 <<-EOSQL
    CREATE ROLE ${PG_USER} WITH LOGIN SUPERUSER PASSWORD '${PG_PASSWORD}';
EOSQL
  psql -v ON_ERROR_STOP=1 --port "${PG_PORT}" -d template1 <<-EOSQL
    CREATE DATABASE ${PG_DATABASE} OWNER ${PG_USER};
EOSQL
  psql -v ON_ERROR_STOP=1 --port "${PG_PORT}" --dbname "${PG_DATABASE}" <<-EOSQL
    CREATE EXTENSION IF NOT EXISTS vector;
EOSQL
fi

echo "installing python requirements"
pip install -r requirements.txt

echo "installing benchmate itself"
pip install .

echo "Done!"





