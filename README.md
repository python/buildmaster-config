# buildmaster-config

[Buildbot](https://buildbot.net/) master configuration for
[buildbot.python.org](http://buildbot.python.org/all/).

[![Build Status](https://travis-ci.org/python/buildmaster-config.svg?branch=master)](https://travis-ci.org/python/buildmaster-config)

## Private settings

The production server uses /etc/buildbot/settings.yaml configuration file which
contains secrets like the IRC nickname password.

## Update requirements

Run locally:

    make regen-requirements

Create a PR. Merge the PR. Then recreate the venv on the server:

    make stop-master
    mv venv old-venv
    make venv
    make start-master

Upgrading buildbot sometimes requires to run the command:

    ./venv/bin/buildbot upgrade-master /data/buildbot/master

Make sure that the server is running, and then remove the old virtual environment:

    rm -rf old-venv

## Hosting

The buildbot master is hosted on the PSF Infrastructure and is managed via
[salt](https://github.com/python/psf-salt/blob/master/salt/buildbot/init.sls).

psycopg2 also requires libpq-dev:

    sudo apt-get install libpq-dev

- Backend host address is `buildbot.nyc1.psf.io`.
- The host is behind the PSF HaProxy cluster which is CNAMEd by `buildbot.python.org`.
- Database is hosted on a managed Postgres cluster, including backups.
- Remote backups of `/etc/buildbot/settings.yaml` are taken hourly and retained for 90 days.
- No other state for the buildbot host is backed up!

Configurations from this repository are applied from the `master` branch on
a `*/15` cron interval using the `update-master` target in `Makefile`.

Python 3.9 is installed manually using ``pyenv`` (which was also installed
manually). Commands to install Python 3.9:

    pyenv update
    pyenv install 3.9.1
    pyenv global 3.8.1 3.9.1


## Add a worker

The list of workers is stored in `/etc/buildbot/settings.yaml` on the server.
A worker password should be made of 14 characters (a-z, A-Z, 0-9 and special
characters), for example using KeePassX.

Documentation: http://docs.buildbot.net/current/manual/configuration/workers.html#defining-workers
