__version__ = '0.1'
__author__ = 'Javier Chavez'

import base64
import hashlib
import os
import datetime

import requests
import simplejson as json
import falcon
import boto3

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.schedulers.base import STATE_RUNNING
from apscheduler.triggers.cron import CronTrigger


from envronment import DEBUG, endpoints
from mako.template import Template
from mako.lookup import TemplateLookup



WORKER_ID = "worker1"
LOCATION = " http://status.javierc.io"
template_lookup = TemplateLookup(directories=['/templates','.'])
scheduler = BackgroundScheduler()

client = boto3.client(
    'sns',
    region_name= os.environ["REGION"],
    aws_access_key_id = os.environ["KEY_ID"],
    aws_secret_access_key = os.environ["ACCESS_KEY"]
)
any_api_topic = os.environ["ANY_STATUS"]


def get_html(template, data):
    """Create a rendered response.
    """
    return Template(filename='templates/'+template, lookup=template_lookup).render(data=data)


def check_auth(header):
    """Check if the auth header is valid

    Args:
        header: header from the response object

    Returns:
        True if credentials match
    """
    if header is None or header == "":
        return False

    out = base64.standard_b64decode(header.split(" ")[1])
    if out.decode("utf-8") == os.environ.get("LOGIN"):
        return True
    else:
        return False

def call_url_task(endpoints):
    """ Check all the endpoints

    Iterates though the endpoint that are listed in envronment file
    and checks the status code. It records the reponse time and 
    notifies subscribers if errors are found.

    Args:
        endpoints: the enpoints that are configured in environment file.
    """
    
    try:
        error = 0
        for endpoint in endpoints:
            if DEBUG:
                print("Calling", endpoint.get('location'))
            rsp = requests.get(endpoint.get('location'))
            endpoint['status_code'] = rsp.status_code
            if rsp.status_code != 200:
                error += 1 
            r_time = rsp.elapsed.microseconds/1000
            endpoint['response_time'] = str(int(r_time)) + 'ms'           
    except:
        pass

    if error >= 1:
        response = client.publish(
            TopicArn=any_api_topic,
            Message="There was " + str(error) + " errors.\nMore information at " + LOCATION 
        )

def create_response_body(section_dict, message, status):
    """ Create a wrapper for json response
    """
    _dict = {
        "status": status,
        "message": message,
        "data": section_dict
    }

    return json.dumps(_dict, separators=(',', ':'))


class SubscribeResource(object):
    """ Handle subscribe and link to AWS
    
    Handles the form data and sends information to AWS
    to subscribe user to updates.
    """
    def on_post(self, req, resp):

        resp.content_type = 'text/html'
        protocol = 'email'
        endpoint = req.get_param('email')

        if req.get_param('phone'):
            protocol = 'sms'
            endpoint = req.get_param('phone')

        if not endpoint:
            raise falcon.HTTPSeeOther('/')

        response = client.subscribe(
            TopicArn=any_api_topic,
            Protocol=protocol,
            Endpoint=endpoint
        )

        token = response.get('SubscriptionArn', '')
        resp.status = falcon.HTTP_201
        resp.body = get_html("subscribe.html", token)



class HomeResource(object):
    """ Main page. 
    
    This displays the results of all the endpoints and allows
    poeple to subscribe.
    """
    def on_get(self, req, resp):
        resp.content_type = 'text/html'
        resp.status = falcon.HTTP_200
        resp.body = get_html("index.html", endpoints)


class StatusEndpoint(object):
    """ Status page.
    
    Allows to control workers. Still needs work.
    """
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

# Auto encode form 
api.req_options.auto_parse_form_urlencoded = True

home = HomeResource()
api_status = StatusEndpoint()
subscribe = SubscribeResource()


api.add_route('/status', api_status)
api.add_route('/subscribe', subscribe)
api.add_route('/', home)



