# buildmaster-config

[Buildbot](https://buildbot.net/) master configuration for
[buildbot.python.org](http://buildbot.python.org/all/).

[![Build Status](https://travis-ci.org/python/buildmaster-config.svg?branch=master)](https://travis-ci.org/python/buildmaster-config)

## Private settings

The production server uses /etc/buildbot/settings.yaml configuration file which
contains secrets like the IRC nickname password.

## Update requirements

Run locally:

    make git-update-requirements

Review updated packages, pay attention to buildbot updates. Create a PR. Merge
the PR. The new venv will be recreated automatically on the server.

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

## Add a worker

The list of workers is stored in `/etc/buildbot/settings.yaml` on the server.
A worker password should be made of 14 characters (a-z, A-Z, 0-9 and special
characters), for example using KeePassX.

* Generate a password
* Add the password in `/etc/buildbot/settings.yaml`
* Restart the buildbot server: `make restart-master`

Documentation: http://docs.buildbot.net/current/manual/configuration/workers.html#defining-workers

## Testing changes locally

To test a change to the buildbot code locally, a worker is needed to run jobs.
First create a `settings.yaml` file in the repository root. The settings file controls
how the Builbot master should connect to workers. The simplest setup runs a worker in the
same process as the Buildbot master on the local machine. The local environment must have any
required dependencies for that worker environment. With the settings file created run:

```bash
export PYBUILDBOT_SETTINGS_PATH=$(pwd)/settings.yaml
```

Then, update the settings file to include the following:

```yaml
# Use a local in-process worker
use_local_worker: true
# Use one of the buildfactories found in master/custom/factories.py.
# Here we use the WASI cross build factory. If unspecified, the default
# is to use the UnixBuild factory
local_worker_buildfactory: "Wasm32WasiCrossBuild"
```

Then run

```
make update-master
```

This updates the state database and starts the buildbot master.
You can now open http://localhost:9011/ and use the local Buildbot master web UI.
Under Builds -> Builders there should be one or more builders for the factory
that was configured. After clicking on the relevant builder, clicking on the "force"
button in the upper right corner will start a new build.

Finally, the master can be stopped when no longer needed by running

```
make stop-master
```
