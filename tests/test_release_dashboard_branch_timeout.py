import json
import unittest
from unittest import mock

from custom import release_dashboard as dashboard


class BranchRequestTests(unittest.TestCase):
    def test_branch_request_has_timeout(self):
        page = object.__new__(dashboard.ReleaseDashboard)
        with mock.patch.object(dashboard.urllib.request, 'urlopen') as urlopen:
            urlopen.return_value.__enter__.return_value.read.return_value = json.dumps({})
            page._refresh_branch_info()
        urlopen.assert_called_once_with(dashboard.BRANCHES_URL, timeout=10)
