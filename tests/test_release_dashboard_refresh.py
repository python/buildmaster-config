import tempfile
import threading
import unittest
from unittest import mock

from custom import release_dashboard as dashboard


class ReleaseDashboardTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.dashboard = dashboard.ReleaseDashboard(test_result_dir=self.directory.name)
        self.client = self.dashboard.flask_app.test_client()
        patcher = mock.patch.object(dashboard.threading, 'Thread')
        self.thread = patcher.start()
        self.addCleanup(patcher.stop)

    def test_cold_requests_start_only_one_refresh(self):
        first = self.client.get('/')
        second = self.client.get('/')
        self.assertEqual(first.status_code, 503)
        self.assertEqual(second.headers['Retry-After'], '5')
        self.thread.return_value.start.assert_called_once()

    def test_expired_cache_remains_available_during_refresh(self):
        self.dashboard.cache = ('old page', 0)
        for _ in range(3):
            response = self.client.get('/')
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.data, b'old page')
        self.thread.return_value.start.assert_called_once()

    def test_failed_refresh_preserves_cache_and_delays_retry(self):
        self.dashboard.cache = ('cached', 0)
        self.dashboard.branch_info = {'3.15': {}}
        self.dashboard.refresh_lock.acquire()
        with mock.patch.object(self.dashboard, '_refresh_branch_info'), \
             mock.patch.object(self.dashboard, 'get_release_status', side_effect=RuntimeError('database unavailable')), \
             self.assertLogs(self.dashboard.flask_app.logger, level='ERROR'):
            self.dashboard._refresh('/static/dashboard.css')
        self.assertEqual(self.dashboard.cache, ('cached', 0))
        self.assertFalse(self.dashboard.refresh_lock.locked())
        response = self.client.get('/')
        self.assertEqual(response.data, b'cached')
        self.thread.assert_not_called()

    def test_refresh_uses_app_context_and_replaces_cache(self):
        self.dashboard.branch_info = {'3.15': {}}
        self.dashboard.refresh_lock.acquire()
        def render(stylesheet_url):
            from flask import current_app
            self.assertIs(current_app._get_current_object(), self.dashboard.flask_app)
            return 'new page'
        with mock.patch.object(self.dashboard, '_refresh_branch_info'), \
             mock.patch.object(self.dashboard, 'get_release_status', side_effect=render):
            self.dashboard._refresh('/static/dashboard.css')
        self.assertEqual(self.dashboard.cache[0], 'new page')
        self.assertFalse(self.dashboard.refresh_lock.locked())

    def test_background_render_preserves_stylesheet_mount_path(self):
        self.dashboard.branch_info = {'3.15': {'branch': '3.15', 'status': 'bugfix'}}
        self.dashboard.flask_app.buildbot_api = mock.Mock()
        self.dashboard.flask_app.buildbot_api.dataGet.return_value = []
        self.dashboard.refresh_lock.acquire()
        with mock.patch.object(self.dashboard, '_refresh_branch_info'):
            self.dashboard._refresh('/plugins/wsgi_dashboards/release_status/static/dashboard.css')
        self.assertIsNotNone(self.dashboard.cache)
        self.assertIn('/plugins/wsgi_dashboards/release_status/static/dashboard.css', self.dashboard.cache[0])


class BackgroundRefreshTests(unittest.TestCase):
    def test_refresh_continues_after_http_request_finishes(self):
        page = dashboard.ReleaseDashboard()
        page.branch_info = {'3.15': {}}
        entered = threading.Event()
        release = threading.Event()
        threads = []
        real_thread = threading.Thread

        def make_thread(**kwargs):
            thread = real_thread(**kwargs)
            threads.append(thread)
            return thread

        def render(stylesheet_url):
            entered.set()
            if not release.wait(5):
                raise RuntimeError('Refresh did not receive release event')
            return 'ready'

        try:
            with mock.patch.object(dashboard.threading, 'Thread', side_effect=make_thread), \
                 mock.patch.object(page, '_refresh_branch_info'), \
                 mock.patch.object(page, 'get_release_status', side_effect=render):
                client = page.flask_app.test_client()
                self.assertEqual(client.get('/').status_code, 503)
                self.assertTrue(entered.wait(5))
                self.assertEqual(client.get('/').status_code, 503)
                self.assertEqual(len(threads), 1)
                release.set()
                threads[0].join(5)
                self.assertFalse(threads[0].is_alive())
                self.assertEqual(client.get('/').data, b'ready')
        finally:
            release.set()
            for thread in threads:
                thread.join(5)
