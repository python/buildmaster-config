PYTHON_VERSION=3.13
SYSTEM_PYTHON=python$(PYTHON_VERSION)
VENV_DIR=./venv
REQUIREMENTS=requirements-$(PYTHON_VERSION).txt
PIP=$(VENV_DIR)/bin/pip
# make stop-server kills all processes named "python"
PKILL_NAME="python"
BUILDBOT=$(VENV_DIR)/bin/buildbot
VENV_CHECK=$(VENV_DIR)/lib/python$(PYTHON_VERSION)/site-packages/buildbot/master.py
USER=buildbot
LOGLINES=50

# Setup targets

.PHONY: venv regen-requirements

venv: $(VENV_CHECK)

clean:
	rm -rf venv

$(VENV_CHECK): $(REQUIREMENTS)
	$(SYSTEM_PYTHON) -m venv --clear venv
	$(PIP) install -U pip
	$(PIP) install -r $(REQUIREMENTS)

regen-requirements:
	$(SYSTEM_PYTHON) -m venv --clear venv
	$(PIP) install -U pip
	$(PIP) install -U -r requirements.in
	$(PIP) freeze > $(REQUIREMENTS)

# Test targets

.PHONY: check

check: $(VENV_CHECK)
	$(BUILDBOT) checkconfig master

# Management targets

.PHONY: update-master start-master restart-master stop-master

update-master: stop-master
	@if [ `git rev-parse --symbolic-full-name HEAD` = "refs/heads/main" ]; \
	then \
		git pull; \
	else \
		echo "Not on main, not pulling updates"; \
	fi
	$(MAKE) run-target TARGET=upgrade-master LOGLINES=0
	$(MAKE) check
	$(MAKE) start-master

start-master: TARGET=start
start-master: run-target

restart-master: TARGET=restart
restart-master: run-target

stop-master: TARGET=stop
stop-master: run-target
	# issue #384: sometimes when "buildbot stop master" sends SIGINT to
	# Twisted, the server goes in a broken state: it's being "shut down",
	# but it never completes. The server stays forever in this state: it is
	# still "running" but no longer schedules new jobs. Kill the process
	# to make sure that it goes bad to a known state (don't run anymore).
	echo "Buildbot processes (look for process name: $(PKILL_NAME))"
	pgrep -u $(USER) $(PKILL_NAME) ||:
	echo "Send SIGKILL to remaining buildbot processes (if any)"
	pkill -KILL -u $(USER) $(PKILL_NAME) ||:

run-target: $(VENV_CHECK)
	$(BUILDBOT) $(TARGET) master; tail -n$(LOGLINES) master/twistd.log

git-update-requirements:
	git switch main
	git pull
	git switch -c reqs main
	make regen-requirements
	git ci -a -m "run make regen-requirements"
