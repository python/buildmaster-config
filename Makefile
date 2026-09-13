PYTHON_VERSION=3.13
SYSTEM_PYTHON=python$(PYTHON_VERSION)
VENV_DIR=./venv
REQUIREMENTS=requirements-$(PYTHON_VERSION).txt
PIP=$(VENV_DIR)/bin/pip
BUILDBOT=$(VENV_DIR)/bin/buildbot
VENV_CHECK=$(VENV_DIR)/lib/python$(PYTHON_VERSION)/site-packages/buildbot/master.py
LOGLINES=50

# Setup targets

.PHONY: venv regen-requirements

## venv              Create a venv with necessary tools
venv: $(VENV_CHECK)

## clean             Remove the venv
clean:
	rm -rf venv

$(VENV_CHECK): $(REQUIREMENTS)
	$(SYSTEM_PYTHON) -m venv --clear venv
	$(PIP) install -U pip
	$(PIP) install -r $(REQUIREMENTS)

## regen-requirements Regenerate pinned requirements file
regen-requirements:
	$(SYSTEM_PYTHON) -m venv --clear venv
	$(PIP) install -U pip
	$(PIP) install -U --uploaded-prior-to=P5D -r requirements.in
	$(PIP) freeze > $(REQUIREMENTS)

# Test targets

.PHONY: check

## check             Validate buildbot master configuration
check: $(VENV_CHECK)
	$(BUILDBOT) checkconfig master

# Management targets

.PHONY: update-master start-master restart-master stop-master

## update-master     Pull updates, upgrade, check config, and start master
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

## start-master      Start the buildbot master
start-master: TARGET=start
start-master: run-target

## restart-master    Restart the buildbot master
restart-master: TARGET=restart
restart-master: run-target

# Exits successfully when master/twistd.pid names a running buildbot master.
PID_IS_MASTER = pid=$$(cat master/twistd.pid 2>/dev/null); \
	case "$$pid" in \
		''|*[!0-9]*) false;; \
		*) ps -o args= -p "$$pid" 2>/dev/null | grep -q buildbot.tac;; \
	esac

## stop-master       Stop the buildbot master
stop-master: $(VENV_CHECK)
	# issue #384: sometimes when "buildbot stop master" sends SIGTERM to
	# Twisted, the server goes in a broken state: it's being "shut down",
	# but it never completes. The server stays forever in this state: it is
	# still "running" but no longer schedules new jobs. Kill the process
	# to make sure that it goes back to a known state (don't run anymore).
	# Validate the pid first, since buildbot stop signals it blindly, and
	# afterwards kill only that pid, not every python process of this user.
	@if [ -f master/twistd.pid ] && ! { $(PID_IS_MASTER); }; then \
		echo "Ignoring stale master/twistd.pid: $$pid is not a buildbot master"; \
		rm -f master/twistd.pid; \
	fi
	$(BUILDBOT) stop master; tail -n$(LOGLINES) master/twistd.log
	@echo "Python processes of the buildbot user:"
	@pgrep -a -u buildbot python ||:
	@if { $(PID_IS_MASTER); }; then \
		echo "Sending SIGKILL to remaining buildbot process $$pid"; \
		kill -KILL "$$pid" ||:; \
	else \
		echo "No buildbot master left to kill"; \
	fi

run-target: $(VENV_CHECK)
	$(BUILDBOT) $(TARGET) master; tail -n$(LOGLINES) master/twistd.log

## git-update-requirements Create a branch with regenerated requirements
git-update-requirements:
	git switch main
	git pull
	git switch -c reqs main
	make regen-requirements
	git commit -a -m "Run make regen-requirements"

.PHONY: help
help : Makefile
	@echo "Use \`make <target>' where <target> is one of"
	@sed -n 's/^##//p' $<
