# buildmaster-config

[Buildbot](https://buildbot.net/) master configuration for
[buildbot.python.org](https://buildbot.python.org/).

[![Check config](https://github.com/python/buildmaster-config/actions/workflows/check.yml/badge.svg)](https://github.com/python/buildmaster-config/actions/workflows/check.yml)

> [!NOTE]
> This README has instructions for Buildbot administrators.
> User guides are in the Devguide:
> - [Working with buildbots](https://devguide.python.org/testing/buildbots/)
> - [New buildbot workers](https://devguide.python.org/testing/new-buildbot-worker/)


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
[salt](https://github.com/python/psf-salt/blob/main/salt/buildbot/init.sls).

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

To add a worker, people follow the [Devguide](https://devguide.python.org/testing/new-buildbot-worker/)
which directs them to an issue template to fill out.
Make sure you have all the info the template asks for.

If the owner did not request a new password (that is, they're reusing one
from an existing worker):

* Make a PR (or ask the new owner to make a PR) that adds the worker to
  `master/custom/workers.py`, with the owner username as first component.
* Check `/etc/buildbot/settings.yaml` on the server: the email and GitHub
  username should match.
* Merge the PR.
* Watch the logs; wait for Salt to pull the PR and restart the server.
* Close the issue. You're done.

When adding a new owner, or a new worker password for an existing owner,
do the following first:

* Generate a password using e.g.:

      import secrets
      print(secrets.token_urlsafe(14))

* Check the username doesn't already exist in `/etc/buildbot/settings.yaml`.
* Add an owner entry to `/etc/buildbot/settings.yaml`.
* Check the config using `make check` (on the server).
* E-mail the password to the new owner.
* As above: add the worker to `master/custom/workers.py`; merge; restart.


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
