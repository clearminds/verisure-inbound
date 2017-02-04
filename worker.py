import verisure
import configparser
import os

config = configparser.ConfigParser()
config.read('.cache.cfg')
if not 'verisure' in config.sections():
    config.add_section('verisure')


session = verisure.Session(os.environ['VERISURE_EMAIL'], os.environ['VERISURE_PASSWORD'])
session.login()

import paho.mqtt.client as mqtt
def domoticz_publish(message):
    client.publish("domoticz/in", message)

def process_overview():
    try:
        overview = session.get_overview()
    except:
        session.login()
        overview = session.get_overview()

    armStatus = overview['armState']
    if armStatus['statusType'] == 'ARMED_AWAY':
        armState = 4
    elif armStatus['statusType'] == 'ARMED_HOME':
        armState = 3
    else:
        armState = 1

    try:
        old_armState = config.getint('verisure', 'armState')
    except:
        old_armState = None
    if isinstance(armState, int) and armState != old_armState:
        config.set('verisure', 'armState', str(armState))
        domoticz_publish('{"command":"udevice","idx":%s,"nvalue":%s,"svalue":"%s"}' % (os.environ['DOMOTICZ_IDX_ARMSTATE'], armState, armStatus['statusType']))

    doorStatus = overview['doorLockStatusList'][0]
    doorState = doorStatus['currentLockState']
    if doorState == 'LOCKED':
        doorState = False
    else:
        doorState = True

    try:
        old_doorState = config.getboolean('verisure', 'doorState')
    except:
        old_doorState = None
    if isinstance(doorState, bool) and doorState != old_doorState:
        config.set('verisure', 'doorState', str(doorState))
        if doorState:
            domoticz_publish('{"idx":%s,"command":"switchlight","switchcmd":"On"}' % (os.environ['DOMOTICZ_IDX_DOOR']))
        else:
            domoticz_publish('{"idx":%s,"command":"switchlight","switchcmd":"Off"}' % (os.environ['DOMOTICZ_IDX_DOOR']))

    print "Current armState: %s - %s, Current doorState: %s" % (armState, armStatus['statusType'], doorState)
    with open('.cache.cfg', 'w') as configfile:
        config.write(configfile)

    return True

# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, rc):
    print("Connected - Starting to process data")
    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe("verisure")

# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    print(msg.topic+" "+str(msg.payload))
    process_overview()
    if msg.payload.startswith('doorman/'):
        print "os.execute()"

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.username_pw_set(os.environ['MQTT_USERNAME'], password=os.environ['MQTT_PASSWORD'])
client.connect(os.environ['MQTT_HOST'], 1883, 5)


# Blocking call that processes network traffic, dispatches callbacks and
# handles reconnecting.
# Other loop*() functions are available that give a threaded interface and a
# manual interface.
client.loop_forever()

session.logout()
