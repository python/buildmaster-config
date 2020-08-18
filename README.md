# buildmaster-config

[Buildbot](https://buildbot.net/) master configuration for
[buildbot.python.org](http://buildbot.python.org/all/).

[![Build Status](https://travis-ci.org/python/buildmaster-config.svg?branch=master)](https://travis-ci.org/python/buildmaster-config)

## Update requirements

To run locally:

    make regen-requirements
    # create a pull request to update requirements.txt

## Hosting

The buildbot master is hosted on the PSF Infrastructure and is managed via
[salt](https://github.com/python/psf-salt/blob/master/salt/buildbot/init.sls).

- Backend host address is `buildbot.nyc1.psf.io`.
- The host is behind the PSF HaProxy cluster which is CNAMEd by `buildbot.python.org`.
- Database is hosted on a managed Postgres cluster, including backups.
- Remote backups of `/etc/buildbot/settings.yaml` are taken hourly and retained for 90 days.
- No other state for the buildbot host is backed up!

Configurations from this repository are applied from the `master` branch on
a `*/15` cron interval using the `update-master` target in `Makefile`.

## Add a worker

The list of workers is stored in `/etc/buildbot/settings.yaml` on the server.
A worker password should be made of 14 characters (a-z, A-Z, 0-9 and special
characters), for example using KeePassX.

Documentation: http://docs.buildbot.net/current/manual/configuration/workers.html#defining-workers
