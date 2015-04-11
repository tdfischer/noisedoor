#!/usr/bin/env python
import calendar
import datetime
import json
import logging
import requests
import os

import settings

def log_event(event):
    logging.debug('Got event %s', event['type'])
    try:
        db  = json.loads(open('access.log', 'r').read())
    except IOError:
        db = []
    db.append({
        'receiveTime': calendar.timegm(datetime.datetime.utcnow().timetuple()),
        'event': event
    })
    with open('access.log~', 'w') as f:
        f.write(json.dumps(db))
    os.rename('access.log~', 'access.log')

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

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    run_stream()
