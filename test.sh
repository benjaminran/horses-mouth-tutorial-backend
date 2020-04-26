#!/usr/bin/env bash


set -x
# show topics is empty
curl 'http://localhost:5000/topics/'

# register a couple topics
curl -H 'Content-Type: application/json' -d '{"name": "foo", "description": "bar baz qux"}' 'http://localhost:5000/topics/'
curl -H 'Content-Type: application/json' -d '{"name": "corge", "description": "norg garply", "sound": "https://drive.google.com/uc?export=download&id=12f_p8mGcdmE1g9N5RJqlnzxfOMBq5fr_"}' 'http://localhost:5000/topics/' | tee /tmp/backup-test.corge.out

id=`cat /tmp/backup-test.corge.out | jq .topic.id | sed 's/"//g'`

# publish an event to the topic
curl -XPUT "http://localhost:5000/topics/$id" | tee /tmp/backup-test.corge-put.out

put_time=`cat /tmp/backup-test.corge.out | jq .time`

# query the topic, first with no start time then with start time that should exclude the put done
curl "http://localhost:5000/topics/$id"
curl "http://localhost:5000/topics/${id}?after=${put_time}"
