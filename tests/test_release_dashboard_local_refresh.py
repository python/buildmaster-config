import unittest

from flask import Flask

from custom import release_dashboard as dashboard


class LocalRefreshTests(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)

    def test_proxy_cannot_force_refresh(self):
        with self.app.test_request_context('/?refresh=true', headers={'X-Forwarded-For': '203.0.113.1'}, environ_overrides={'REMOTE_ADDR': '127.0.0.1'}):
            self.assertFalse(dashboard._is_local_refresh())

    def test_remote_address_cannot_force_refresh(self):
        with self.app.test_request_context('/?refresh=true', environ_overrides={'REMOTE_ADDR': '203.0.113.1'}):
            self.assertFalse(dashboard._is_local_refresh())

    def test_loopback_can_force_refresh(self):
        with self.app.test_request_context('/?refresh=true', environ_overrides={'REMOTE_ADDR': '127.0.0.1'}):
            self.assertTrue(dashboard._is_local_refresh())

    def test_loopback_without_refresh_flag_does_not_force_refresh(self):
        with self.app.test_request_context('/', environ_overrides={'REMOTE_ADDR': '127.0.0.1'}):
            self.assertFalse(dashboard._is_local_refresh())
