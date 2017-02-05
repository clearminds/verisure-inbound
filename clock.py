# -*- coding: utf-8 -*-
import os
import paho.mqtt.publish as publish
from apscheduler.schedulers.blocking import BlockingScheduler

sched = BlockingScheduler()

interval = os.environ.get('VERISURE_CRON_INTERVAL', 60)
if interval.isdigit():
    interval = int(interval)
else:
    print('Invalid VERISURE_CRON_INTERVAL. Using default 60')
    interval = 60

print('Starting poll with an interval on %s seconds' % interval)


@sched.scheduled_job('interval', seconds=interval)
def poll_verisure():
    publish.single('verisure', 'cron', hostname=os.environ['MQTT_HOST'],
                   auth={'username': os.environ['MQTT_USERNAME'],
                         'password': os.environ['MQTT_PASSWORD']})

sched.start()
