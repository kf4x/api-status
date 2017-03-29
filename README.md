# API Status Page and Monitor

Uses the super fast Falcon framework with Advanced python scheduler.

##### Why
Status pages are expensive! So I created this for my projects.
You can see it [running live](http://status.javierc.io/)

##### How
This is a small app that pings API endpoints and checks response.
If the response is not 200 then it notifies subscribers using [AWS SNS](https://aws.amazon.com/sns/).

Currently you can subscribe to get alerts via **email** or **SMS**.


Meant to be small lightweight. **Yes** the css is not great,
but I didnt want to add exernal libs.

# Overview of Endpoints

Endpoint | Description
-------- | -----------
``/status`` | Get the status of the API
``/`` | Get the overview of all the endpoints 

# Setup

This is built against python 3.5 and Cython! 

Create a new venv and install deps.

```bash
virtualenv <env_name> --python=python3
pip install -r requirements.txt
```

Open ``environment.py`` file and fill in
* ``DEBUG`` turn on debug mode
* ``endpoints`` list of endpoints to check 


You will need environment variables.

```bash
REGION=region
KEY_ID=key_id
ACCESS_KEY=secret_access
ANY_STATUS=arn
LOGIN=username:password
```


# Running

Spin up Gunicorn and run. 
Note that production is ran with uwsgi

```bash
gunicorn app
```


---
Author: Javier

Email: <youracow@gmail.com>
