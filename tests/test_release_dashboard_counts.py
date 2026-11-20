import unittest
from types import SimpleNamespace
from unittest import mock

from custom import release_dashboard as dashboard


class DashboardCountsTests(unittest.TestCase):
    def test_count_option_is_used_only_when_supported(self):
        api = mock.Mock()
        state = dashboard.DashboardState(SimpleNamespace(flask_app=SimpleNamespace(buildbot_api=api)))
        for supported in (False, True):
            with self.subTest(supported=supported):
                api.reset_mock()
                with mock.patch.object(dashboard, 'SUPPORTS_INCLUDE_TOTAL', supported):
                    state.dataGet(('builds',), limit=200)
                expected = {'limit': 200}
                if supported:
                    expected['include_total'] = False
                api.dataGet.assert_called_once_with(('builds',), **expected)
