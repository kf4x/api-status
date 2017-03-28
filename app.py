import base64
import hashlib
import os
import datetime

import requests
import simplejson as json
import falcon


from apscheduler.schedulers.background import BackgroundScheduler

from apscheduler.schedulers.base import STATE_RUNNING
from apscheduler.triggers.cron import CronTrigger


from envronment import server_key, auth, DEBUG, endpoints


from mako.template import Template
from mako.lookup import TemplateLookup


# Constants
WORKER_ID = "worker1"
template_lookup = TemplateLookup(directories=['/templates','.'])
scheduler = BackgroundScheduler()



def get_html(template, data):
    """Create a rendered response.
    """
    return Template(filename='templates/'+template, lookup=template_lookup).render(data=data)


def check_auth(header):
    if header is None or header == "":
        return False

    out = base64.standard_b64decode(header.split(" ")[1])
    if out.decode("utf-8") == auth:
        return True
    else:
        return False



def call_url_task(endpoints):

    try:
        for endpoint in endpoints:
            if DEBUG:
                print("Calling", endpoint.get('location'))
            rsp = requests.get(endpoint.get('location'))
            endpoint['status_code'] = rsp.status_code
            r_time = rsp.elapsed.microseconds/1000
            endpoint['response_time'] = str(int(r_time)) + 'ms'
    except:
        pass

def create_response_body(section_dict, message, status):
    _dict = {
        "status": status,
        "message": message,
        "data": section_dict
    }

    return json.dumps(_dict, separators=(',', ':'))


class HomeResource(object):

    def on_get(self, req, resp):
        resp.content_type = 'text/html'
        resp.status = falcon.HTTP_200
        resp.body = get_html("index.html", endpoints)


class StatusEndpoint(object):

    def on_get(self, req, resp):

        _q = req.params.get('update', '')
        if not DEBUG:
            is_valid = check_auth(req.auth)
        else:
            is_valid = True
        _data = {}

        if is_valid and _q == "start":

            if scheduler.get_job(WORKER_ID) is None:
                scheduler.add_job(call_url_task,
                                  name="API Status Worker",
                                  id=WORKER_ID,
                                  trigger=CronTrigger(second='*/45'),
                                  args=(endpoints,))
            # Check state
            if scheduler.state != STATE_RUNNING:
                scheduler.start()

        elif is_valid:
            resp.content_type = 'application/json'
            resp.status = falcon.HTTP_200
            job = scheduler.get_job(WORKER_ID)

            _data = {
                "scheduled": job.next_run_time.isoformat() if job else None,
                "last_update": ""
            }
        else:
            _data = {
                "last_update":""
            }

        resp.body = create_response_body(_data, "", resp.status)


api = application = falcon.API()
home = HomeResource()
api_status = StatusEndpoint()

api.add_route('/status', api_status)
api.add_route('/', home)



