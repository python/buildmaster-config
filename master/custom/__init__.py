MAIN_BRANCH_VERSION = "3.14"
CUSTOM_BRANCH_NAME = "custom"
# The Git branch is called "main", but we give it a different name in buildbot.
# See git_branches in master/master.cfg.
MAIN_BRANCH_NAME = "3.x"

# JUnit XML is disabled for now (2024-07-01) since nobody is using the output
#JUNIT_FILENAME = "test-results.xml"
JUNIT_FILENAME = None
