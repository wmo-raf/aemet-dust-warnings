#!/bin/sh

echo "Setup Schema"
flask setup_schema

echo "Running Migrations"
flask db upgrade

echo "Create PG Function"
flask create_pg_function

#ensure environment-variables are available for cronjob
printenv | grep -v "no_proxy" >>/etc/environment

# ensure cron is running
service cron start
service cron status

exec "$@"
