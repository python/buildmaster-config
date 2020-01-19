import re

TESTS_STEP = "test"

TRACEBACK_REGEX = re.compile(
    r"""
     Traceback # Lines containing "Traceback"
     [\s\S]+? # Match greedy any text (preserving ASCII flags).
     (?=^(?:\d|test|\Z|\n|ok)) # Stop matching in lines starting with
                               # a number (log time), "test" or the end
                               # of the string.
    """,
    re.MULTILINE | re.VERBOSE,
)

LEAKS_REGEX = re.compile(r"(test_\w+) leaked \[.*] (.*),.*", re.MULTILINE)


class Logs:
    def __init__(self, raw_logs):
        self._logs = raw_logs

    @property
    def raw_logs(self):
        return self._logs

    def _get_test_results(self, header):
        test_regexp = re.compile(
            rf"""
             ^\d+\s{header}: # Lines starting with "header"
             [\s\S]+? # Match greedy any text (preserving ASCII flags).
             (?=^(?:\d|test|\Z|Total)) # Stop matching in lines starting with
                                       # a number (log time), "test" or the end
                                       # of the string.
            """,
            re.MULTILINE | re.VERBOSE,
        )

        failed_blocks = list(set(test_regexp.findall(self._logs)))
        if not failed_blocks:
            return set()
        # Pick the last re-run of the test
        block = failed_blocks[-1]
        tests = []
        for line in block.split("\n")[1:]:
            if not line:
                continue
            test_names = line.split(" ")
            tests.extend(test for test in test_names if test)
        return set(tests)

    def get_tracebacks(self):
        yield from set(TRACEBACK_REGEX.findall(self._logs))

    def get_leaks(self):
        for test_name, resource in set(LEAKS_REGEX.findall(self._logs)):
            yield test_name, resource

    def get_failed_tests(self):
        yield from set(self._get_test_results(r"tests?\sfailed"))

    def get_rerun_tests(self):
        yield from set(self._get_test_results(r"re-run\stests?"))

    def get_failed_subtests(self):
        failed_subtest_regexp = re.compile(
            r"=+"  # Decoration prefix
            r"\n[A-Z]+:"  # Test result (e.g. FAIL:)
            r"\s(\w+)\s"  # test name (e.g. test_tools)
            r"\((.*?)\)"  # subtest name (e.g. test.test_tools.test_unparse.DirectoryTestCase)
            r".*"  # Trailing text (e.g. filename)
            r"\n*"  # End of the line
            r".*"  # Maybe some test description
            r"-+",  # Trailing decoration
            re.MULTILINE | re.VERBOSE,
        )
        for test, subtest in set(failed_subtest_regexp.findall(self._logs)):
            yield test, subtest

    def test_summary(self):
        result_start = [
            match.start() for match in re.finditer("== Tests result", self._logs)
        ]
        if not result_start:
            return ""
        result_start = result_start[-1]
        result_end = [
            match.start() for match in re.finditer("Tests result:", self._logs)
        ]
        if not result_end:
            return ""
        result_end = result_end[-1]
        return self._logs[result_start:result_end]

    def format_failing_tests(self):

        text = []
        failed = list(self.get_failed_tests())
        if failed:
            text.append("Failed tests:\n")
            text.extend([f"- {test_name}" for test_name in failed])
            text.append("")
        failed_subtests = list(self.get_failed_subtests())
        if failed_subtests:
            text.append("Failed subtests:\n")
            text.extend([f"- {test} - {subtest}" for test, subtest in failed_subtests])
            text.append("")
        leaked = list(self.get_leaks())
        if leaked:
            text.append("Test leaking resources:\n")
            text.extend(
                [f"- {test_name}: {resource}" for test_name, resource in leaked]
            )
            text.append("")
        return "\n".join(text)


def construct_tracebacks_from_build_stderr(build):
    for step in build["steps"]:
        try:
            test_log = step["logs"][0]["content"]["content"]
        except IndexError:
            continue
        test_log = "\n".join(
            [line.lstrip("e") for line in test_log.splitlines() if line.startswith("e")]
        )
        if not test_log:
            continue
        yield test_log


def get_logs_and_tracebacks_from_build(build):
    test_log = ""
    try:
        test_step = [step for step in build["steps"] if step["name"] == TESTS_STEP][0]
        test_log = test_step["logs"][0]["content"]["content"]
        test_log = "\n".join([line.lstrip("eo") for line in test_log.splitlines()])
    except IndexError:
        pass
    logs = Logs(test_log)
    tracebacks = list(logs.get_tracebacks())
    if not tracebacks:
        tracebacks = list(construct_tracebacks_from_build_stderr(build))
    return logs, tracebacks
