#!/bin/sh

if [ ! -d /opt/architect ]
then
  mkdir -p /opt/architect
fi

/usr/local/architect/util/manage.py migrate

/usr/local/architect/util/testData docker

/usr/local/architect/cron/planEvaluate
