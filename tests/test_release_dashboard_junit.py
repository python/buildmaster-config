import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from custom import release_dashboard as dashboard


class JUnitResultsTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.folder = Path(self.directory.name) / '3.15' / 'builder'
        self.folder.mkdir(parents=True)

    def read_results(self, text):
        (self.folder / 'build_1.xml').write_text(text)
        app = SimpleNamespace(test_result_dir=Path(self.directory.name))
        parent = SimpleNamespace(_root=SimpleNamespace(_app=app))
        build = dashboard.Build(parent, {'number': 1})
        class Builder:
            branch = SimpleNamespace(tag='3.15')
            def __getitem__(self, key):
                return 'builder'
        build.__dict__['builder'] = Builder()
        return build.junit_results

    def test_errors_keep_their_details(self):
        result = self.read_results('<testsuites><testsuite><testcase name="test.passing" />'
            '<testcase name="test.module.method"><error type="AssertionError">details</error>'
            '</testcase></testsuite></testsuites>')
        self.assertEqual(result.error_types, {'AssertionError'})
        error = result.contents['module'].contents['method'].errors[0]
        self.assertEqual(error['text'], 'details')

    def test_successful_cases_have_no_errors(self):
        result = self.read_results('<testsuites><testsuite><testcase name="test.passing" /></testsuite></testsuites>')
        self.assertEqual(result.contents, {})

    def test_malformed_xml_does_not_return_partial_results(self):
        result = self.read_results('<testsuite><testcase name="test.module.method"><error type="ValueError">details</error></testcase>')
        self.assertIsNone(result)
