PYTHON_VERSION=3.9
SYSTEM_PYTHON=python$(PYTHON_VERSION)
VENV_DIR=./venv
PIP=$(VENV_DIR)/bin/pip
BUILDBOT=$(VENV_DIR)/bin/buildbot
VENV_CHECK=$(VENV_DIR)/lib/python$(PYTHON_VERSION)/site-packages/buildbot/master.py
LOGLINES=50

# Setup targets

.PHONY: venv regen-requirements

venv: $(VENV_CHECK)

clean:
	rm -rf venv

$(VENV_CHECK): requirements.txt
	$(SYSTEM_PYTHON) -m venv --clear venv
	$(PIP) install -U pip setuptools wheel
	$(PIP) install -r requirements.txt

regen-requirements:
	$(SYSTEM_PYTHON) -m venv --clear venv
	$(PIP) install -U pip setuptools wheel
	$(PIP) install -U -r requirements.in
	$(PIP) freeze > requirements.txt

# Test targets

.PHONY: check

check: $(VENV_CHECK)
	$(BUILDBOT) checkconfig master/master.cfg

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

run-target: $(VENV_CHECK)
	$(BUILDBOT) $(TARGET) master; tail -n$(LOGLINES) master/twistd.log
