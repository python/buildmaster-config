import os
import secrets

import yaml
from twisted.python import log


DEFAULTS = dict(
    web_port=9011,
    worker_port=9021,
    irc_notice=False,
    irc_host="irc.libera.chat",
    irc_channel="#python-dev-notifs",
    irc_nick="py-bb-test",
    buildbot_url="http://localhost:9011/",
    db_url="sqlite:///state.sqlite",
    do_auth=False,
    send_mail=False,
    status_email="example@example.org",
    email_relay_host="mail.example.org",
    from_email="buildbot@example.org",
    verbosity=1,
    git_url="https://github.com/python/cpython",
    use_local_worker=False,
)


class Settings:

    value = ...
    path = None

    def __init__(self, value=..., path=None):
        if value is not ...:
            self.value = value
        self.path = path or []

    @classmethod
    def from_file(cls, filename):
        with open(filename) as f:
            return cls(yaml.full_load(f), path=[])

    def __getitem__(self, key):
        path_key = real_key = key
        if isinstance(key, type(self)):
            path_key = real_key = key.value
            if real_key is ...:
                real_key = "unknown"
                path_key = key.path
        new_path = self.path + [path_key]
        if self.value is not ... and real_key in self.value:
            value = self.value[real_key]
            if isinstance(value, (list, dict)):
                return type(self)(value, path=new_path)
            return value
        return type(self)(path=new_path)

    __getattr__ = __getitem__

    def get(self, key, default=...):
        if self.value is not ...:
            value = self.value.get(key, default)
            if value is not ...:
                return value
        if default is not ...:
            return default
        return type(self)(path=self.path + [key])

    def _convert(self, func, default):
        if self.value is not ...:
            return func(self.value)
        default = DEFAULTS.get(".".join(map(str, self.path)), default)
        if not os.getenv("CI"):
            # Note: We use log.err to make this show up during `checkconfig`
            log.err(f"WARNING: No setting at {self.path}, returning {default}")
        return func(default)

    def __int__(self):
        return self._convert(int, 1)

    def __str__(self):
        return self._convert(str, secrets.token_urlsafe(8))

    def __bool__(self):
        return self._convert(bool, False)
