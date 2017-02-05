# -*- coding: utf-8 -*-
from config import Config
from parse import Parse
from flask import  Flask, request
from werkzeug.contrib.fixers import ProxyFix

import os
from unidecode import unidecode

app = Flask(__name__)

config = Config()

import paho.mqtt.publish as publish


def mqtt_publish(dest, msg):
    publish.single(dest, msg, hostname=os.environ['MQTT_HOST'],
                   auth={'username': os.environ['MQTT_USERNAME'],
                         'password': os.environ['MQTT_PASSWORD']})


@app.route('/ping', methods=['GET'])
def ping():
    return "Pong!"


@app.route(config.endpoint, methods=['POST'])
def inbound_parse():
    parse = Parse(config, request)
    to = parse.key_values().get('to')
    dkim = parse.key_values().get('dkim')
    sender = parse.key_values().get('from')
    subject = unidecode(parse.key_values().get('subject', 'no_subject')).strip().lower()
    if to != os.environ['VERISURE_EMAIL']  or sender != 'Verisure <no-reply@verisure.com>' or dkim != '{@verisure.com : pass}':
        print ('To: ', to)
        print ('Sender: ', sender)
        print ('Subject: ', subject)
        print ('DKIM: ', dkim)
        return "OK"
    if subject == 'larmat':
        mqtt_publish('verisure', 'alarm/on')
    elif subject == 'avlarmat':
        mqtt_publish('verisure', 'alarm/off')
    elif subject == 'upplast utifran':
        mqtt_publish('verisure', 'doorman/unlock/outside')
    elif subject == 'upplast inifran':
        mqtt_publish('verisure', 'doorman/unlock/inside')
    elif subject == 'last inifran':
        mqtt_publish('verisure', 'doorman/lock/inside')
    elif subject == 'last utifran':
        mqtt_publish('verisure', 'doorman/lock/inside')
    elif subject == 'upplast':
        mqtt_publish('verisure', 'doorman/unlock/remote')
    elif subject == u'misslyckad lasning':
        mqtt_publish('verisure', 'doorman/lock/fail')
    else:
        mqtt_publish('verisure', 'unknown/'+subject)
    # Tell SendGrid's Inbound Parse to stop sending POSTs
    # Everything is 200 OK :)
    return "OK"


if __name__ == '__main__':
    # Be sure to set config.debug_mode to False in production
    port = int(os.environ.get("PORT", config.port))
    if port != config.port:
        config.debug = False
    app.wsgi_app = ProxyFix(app.wsgi_app)
    app.run(host='0.0.0.0', debug=config.debug_mode, port=port)
