# buildmaster-config

[Buildbot](https://buildbot.net/) master configuration for
[buildbot.python.org](http://buildbot.python.org/all/).

[![Build Status](https://travis-ci.org/python/buildmaster-config.svg?branch=master)](https://travis-ci.org/python/buildmaster-config)

## Update requirements

To run locally:

    make regen-requirements
    # create a pull request to update requirements.txt

On the server (this method include downtime):

    make stop-master
    mv venv venv.old
    make venv SYSTEM_PYTHON=/usr/local/bin/python3.6
    make start-master

Note: starting the server takes 10 seconds until it answers on HTTP.

## Add a worker

The list of workers is stored in master/local.py on the server. A worker
password should be made of 14 characters (a-z, A-Z, 0-9 and special
characters), for example using KeePassX.

Documentation: http://docs.buildbot.net/current/manual/configuration/workers.html#defining-workers
