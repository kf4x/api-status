# Falcon Application 

This is a small app that pings apis and checks response

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
* ``auth`` basic auth format of usr:pwd
* ``endpoints`` list of endpoints to check 

# Running

Spin up Gunicorn and run. 
Note that production is ran with uwsgi

```bash
gunicorn app
```


---
Author: Javier

Email: <youracow@gmail.com>
