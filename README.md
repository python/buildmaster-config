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

## Master roles

> [!WARNING]
> Only the default `all` role is ready for production. The split roles can
> lose webhooks while the engine is down; do not deploy them yet.

The master can run as one process, or as two masters sharing the database so
that web traffic and worker traffic stop competing for the same reactor.
`master_role` in `/etc/buildbot/settings.yaml` selects what a master does:

| `master_role` | Runs | Serves |
|---|---|---|
| `all` (default) | workers, builders, schedulers, reporters, janitor | web UI, change hooks, dashboards, force scheduler |
| `engine` | same as `all`, subject to `run_janitor` and `run_reporters` | nothing |
| `ui` | nothing | same as `all` |

`engine` and `ui` need a WAMP router such as [crossbar](https://crossbar.io/),
reachable only from the host:

    master_role: engine        # or: ui
    mq_router_url: ws://localhost:1245/ws
    mq_realm: buildbot         # optional
    mq_debug_level: error      # none, critical, error, warn, info, debug, trace

Reporters must run on exactly one master, so set `run_reporters: false` on
every engine but one. The janitor may run anywhere; `run_janitor: false` only
keeps it off a master. Both must be real YAML booleans.

Changing `master_role` or any `mq_*` setting needs a restart, not a reconfig.
`make update-master` does that.

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

### Testing a multi-master split locally

This needs a WAMP router and a database both masters can share. Install
[crossbar](https://crossbar.io/) in its own virtualenv, write a router config
from the [buildbot MQ documentation](https://docs.buildbot.net/current/manual/configuration/global.html)
bound to `127.0.0.1`, and start it:

```bash
python3 -m venv /tmp/crossbar-venv
/tmp/crossbar-venv/bin/pip install crossbar
/tmp/crossbar-venv/bin/crossbar start --cbdir /tmp/cbdir
```

Start a throwaway PostgreSQL (`psycopg2` needs `libpq-dev`; `psycopg2-binary`
works for local testing):

```bash
podman run -d --name bb-test -p 127.0.0.1:15432:5432 \
    -e POSTGRES_PASSWORD=bb -e POSTGRES_USER=bb -e POSTGRES_DB=bb \
    docker.io/library/postgres:17-alpine
```

Give each master a basedir sharing this repository's config:

```bash
for role in engine ui; do
    mkdir -p /tmp/bb-$role
    cp master/buildbot.tac /tmp/bb-$role/
    ln -sfn $(pwd)/master/master.cfg /tmp/bb-$role/master.cfg
    ln -sfn $(pwd)/master/custom     /tmp/bb-$role/custom
done
```

Write one settings file per role, differing only in `master_role` and
`web_port` (`ui` only). Point `git_url` at a small local repository as a plain
path, so builds fail fast and reporters skip GitHub:

```yaml
master_role: engine
db_url: postgresql+psycopg2://bb:bb@127.0.0.1:15432/bb
mq_router_url: ws://127.0.0.1:1245/ws
use_local_worker: true
git_url: /path/to/a/small/throwaway/git/repo
web_port: 8010
buildbot_url: http://127.0.0.1:8010/
```

Then:

```bash
export PYBUILDBOT_SETTINGS_PATH=/path/to/settings-engine.yaml
./venv/bin/buildbot upgrade-master /tmp/bb-engine
./venv/bin/buildbot start /tmp/bb-engine
PYBUILDBOT_SETTINGS_PATH=/path/to/settings-ui.yaml ./venv/bin/buildbot start /tmp/bb-ui
```

Both logs should report `Wamp connection succeed!`. Force a build from the UI
master and check that the engine runs it.
