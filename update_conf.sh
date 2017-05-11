#!/bin/bash
set -e -x
git pull --rebase
git status
./buildbot.sh checkconfig master/master.cfg
./buildbot.sh reconfig master
