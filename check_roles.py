"""Assert what each master_role configures.

checkconfig alone is not enough: buildbot drops several consistency checks
once multiMaster is set, so a misplaced web server would still parse cleanly.
"""

import os
import sys
import tempfile

from buildbot.config.errors import ConfigErrors
from buildbot.config.master import FileLoader

BASEDIR = "master"
ROUTER = "ws://127.0.0.1:1245/ws"

# The janitor contributes schedulers of its own; everything else is ours.
JANITOR_SCHEDULERS = {"__Janitor", "__Janitor_force"}

# What each role must and must not configure.
EXPECTED = {
    "all": {
        "workers": True, "builders": True, "force scheduler": True,
        "worker port": True, "web server": True, "change hook": True,
        "dashboards": True, "reporters": True, "janitor": True,
        "multiMaster": False, "mq": "simple", "mq realm": None,
        "mq debug level": None,
    },
    "engine": {
        "workers": True, "builders": True, "force scheduler": False,
        "worker port": True, "web server": False, "change hook": False,
        "dashboards": False, "reporters": True, "janitor": True,
        "multiMaster": True, "mq": "wamp", "mq realm": "buildbot",
        "mq debug level": "error",
    },
    "ui": {
        "workers": False, "builders": False, "force scheduler": True,
        "worker port": False, "web server": True, "change hook": True,
        "dashboards": True, "reporters": False, "janitor": False,
        "multiMaster": True, "mq": "wamp", "mq realm": "buildbot",
        "mq debug level": "error",
    },
}

# Far below the real fleet, but catches a configuration that came out empty.
MIN_BUILDERS = 100
MIN_WORKERS = 20


def load(settings):
    """Load master.cfg with the given settings file contents."""
    with tempfile.NamedTemporaryFile("w", suffix=".yaml") as f:
        f.write(settings)
        f.flush()
        os.environ["PYBUILDBOT_SETTINGS_PATH"] = f.name
        return FileLoader(BASEDIR, "master.cfg").loadConfig()


def role_settings(role, extra=""):
    router = "" if role == "all" else f"mq_router_url: {ROUTER}\n"
    return f"master_role: {role}\n{router}{extra}"


def actual(config):
    # configurators are not kept on the loaded config: detect the janitor by
    # its schedulers instead
    names = set(config.schedulers)
    return {
        "workers": bool(config.workers),
        "builders": bool(config.builders),
        "force scheduler": "force" in names,
        "worker port": bool(config.protocols.get("pb")),
        "web server": bool(config.www.get("port")),
        # a web server with no hook or no dashboards is not the one we want
        "change hook": bool(config.www.get("change_hook_dialects")),
        "dashboards": "wsgi_dashboards" in config.www.get("plugins", {}),
        "reporters": bool(config.services),
        "janitor": "__Janitor" in names,
        "multiMaster": bool(config.multiMaster),
        "mq": config.mq.get("type", "simple"),
        "mq realm": config.mq.get("realm"),
        "mq debug level": config.mq.get("wamp_debug_level"),
    }


def force_builders(config):
    scheduler = config.schedulers.get("force")
    return set(scheduler.builderNames) if scheduler else set()


def check_invariants(role, config, fail):
    """Guard against a role that is shaped right but empty."""
    names = set(config.schedulers)
    branch_schedulers = names - {"force"} - JANITOR_SCHEDULERS

    # Encodes the current placement, branch schedulers on the engine. That is
    # under review (webhook-loss gap); swap these if the schedulers move.
    if role in ("all", "engine"):
        if len(config.builders) < MIN_BUILDERS:
            fail(f"{role}: only {len(config.builders)} builders")
        if len(config.workers) < MIN_WORKERS:
            fail(f"{role}: only {len(config.workers)} workers")
        if not branch_schedulers:
            fail(f"{role}: no branch schedulers")
    elif branch_schedulers:
        fail(f"{role}: unexpected branch schedulers {sorted(branch_schedulers)}")

    # The force scheduler must offer exactly the configured builders; the
    # janitor adds its own builder after master.cfg has run.
    if role == "all":
        configured = {b.name for b in config.builders} - {"__Janitor"}
        if force_builders(config) != configured:
            missing = configured - force_builders(config)
            extra = force_builders(config) - configured
            fail(f"{role}: force scheduler builders differ, "
                 f"missing {sorted(missing)[:3]}, unexpected {sorted(extra)[:3]}")


def expect_rejected(label, settings, reason, fail):
    try:
        load(settings)
    except ConfigErrors as error:
        if reason in str(error):
            print(f"==> {label} is rejected")
        else:
            fail(f"{label} failed, but not for the expected reason: {error}")
    else:
        fail(f"{label} was accepted")


def main():
    failures = []
    fail = failures.append

    offered = {}
    for role, expected in EXPECTED.items():
        config = load(role_settings(role))
        got = actual(config)
        for key, want in expected.items():
            if got[key] != want:
                fail(f"{role}: expected {key}={want!r}, got {got[key]!r}")
        check_invariants(role, config, fail)
        offered[role] = force_builders(config)
        print(f"==> {role}: " + ", ".join(f"{k}={got[k]}" for k in expected))

    # The ui configures no builders, but must still offer the same set as all.
    if offered["ui"] != offered["all"]:
        missing = offered["all"] - offered["ui"]
        extra = offered["ui"] - offered["all"]
        fail(f"ui force scheduler differs from all: "
             f"missing {sorted(missing)[:3]}, unexpected {sorted(extra)[:3]}")
    else:
        print(f"==> ui offers the same {len(offered['ui'])} builders as all")

    # The two singleton switches must each turn off one thing and only that.
    for flag, key in (("run_reporters", "reporters"), ("run_janitor", "janitor")):
        got = actual(load(role_settings("engine", f"{flag}: false\n")))
        other = "janitor" if key == "reporters" else "reporters"
        if got[key]:
            fail(f"engine with {flag}: false still has {key}")
        if not got[other]:
            fail(f"engine with {flag}: false also lost {other}")
        print(f"==> engine with {flag}: false drops {key}, keeps {other}")

    # use_local_worker must fall back to UnixBuild with no explicit factory.
    if not load(role_settings("engine", "use_local_worker: true\n")).builders:
        fail("use_local_worker without local_worker_buildfactory built no builders")
    else:
        print("==> use_local_worker without an explicit factory loads")

    expect_rejected("an unknown master_role", "master_role: nonsense\n",
                    "must be 'all', 'engine' or 'ui'", fail)
    for role in ("engine", "ui"):
        expect_rejected(f"{role} without mq_router_url", f"master_role: {role}\n",
                        "requires mq_router_url", fail)
    for flag in ("run_reporters", "run_janitor"):
        expect_rejected(f"a quoted boolean for {flag}",
                        role_settings("ui", f'{flag}: "false"\n'),
                        "must be true or false", fail)
    expect_rejected("a non-string mq_realm", role_settings("engine", "mq_realm: true\n"),
                    "must be a string", fail)
    expect_rejected("an unknown mq_debug_level",
                    role_settings("engine", "mq_debug_level: chatty\n"),
                    "must be one of", fail)

    if failures:
        print("\nFAILED:")
        for failure in failures:
            print(f"  {failure}")
        return 1
    print("\n==> all roles OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
