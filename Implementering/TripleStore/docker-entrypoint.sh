#!/bin/bash
#   Licensed to the Apache Software Foundation (ASF) under one or more
#   contributor license agreements.  See the NOTICE file distributed with
#   this work for additional information regarding copyright ownership.
#   The ASF licenses this file to You under the Apache License, Version 2.0
#   (the "License"); you may not use this file except in compliance with
#   the License.  You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

set -e


if [ -f /run/secrets/ADMIN_PASSWORD ] ; then
  ADMIN_PASSWORD=$(cat /run/secrets/ADMIN_PASSWORD)
fi

if [ -n "$ADMIN_PASSWORD" ] ; then
  ADMIN_PASSWORD_HASH=$(echo "$ADMIN_PASSWORD" | java -jar "${FUSEKI_HOME}/shiro-tools-hasher.jar" -pnc)
  export ADMIN_PASSWORD_HASH
  envsubst '${ADMIN_PASSWORD_HASH}' < "$FUSEKI_HOME/shiro.ini" > "$FUSEKI_BASE/shiro.ini"
else
  cp "$FUSEKI_HOME/shiro.ini" "$FUSEKI_BASE/shiro.ini"
fi

exec "$@" &

echo "Waiting for Fuseki to finish starting up..."
until curl --output /dev/null --silent --head --fail http://localhost:3030; do
  sleep 1s
done

# Create datasets from FUSEKI_DATASET_* environment variables
while read env_var
do
    dataset=$(echo "$env_var" | sed 's/^[^=]*=//')
    echo "Creating dataset $dataset"
    curl -s 'http://localhost:3030/$/datasets' \
         -u "admin:${ADMIN_PASSWORD}" \
         -H 'Content-Type: application/x-www-form-urlencoded; charset=UTF-8' \
         --data "dbName=${dataset}&dbType=${TDB_VERSION:-tdb2}"
done < <(printenv | grep "^FUSEKI_DATASET_")

wait
