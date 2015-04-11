#!/usr/bin/env python
import calendar
import datetime
import json
import logging
import requests
import os

import sys

sys.path.append('/etc/')
try:
    import noisedoor_settings as settings
except ImportError:
    print "Missing /etc/noisedoor_settings.py"

def log_event(event):
    logging.debug('Got event %s', event['type'])
    try:
        db  = json.loads(open(settings.DB_PATH, 'r').read())
    except IOError:
        db = []
    db.append({
        'receiveTime': calendar.timegm(datetime.datetime.utcnow().timetuple()),
        'event': event
    })
    with open(settings.DB_PATH+'~', 'w') as f:
        f.write(json.dumps(db))
    os.rename(settings.DB_PATH+'~', settings.DB_PATH)

def slack_notify(string):
    requests.post(settings.SLACK_HOOK,
        data={
            'payload': json.dumps({'text': string})
        })

EVENTS = {
    'trigger-bell': 'Ding dong at the %(target)s door'
}

def handle_event(line):
    event = json.loads(line)
    event.setdefault('IsHistoricEvent', False)
    if event['IsHistoricEvent']:
        return
    log_event(event)
    if event['type'] in EVENTS:
        slack_notify(EVENTS[event['type']] % event)
    else:
        slack_notify('Earl said: ```%s```'%(event))

def run_stream():
    r = requests.get('http://earl:1212/api/events', stream=True)
    buf = ""
    for line in r.iter_content():
        buf += line
        s = buf.split('\n')
        if len(s) == 2:
            handle_event(s[0])
            buf = s[1]
