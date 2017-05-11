#!/bin/bash
set -e -x

ROOT=/data/buildbot

cd $ROOT/buildbot
git checkout pydotorg-0.8.14+
git pull --rebase

cd $ROOT/buildbot/master
cd master
python setup.py install --root /data/buildbot/ --install-lib /lib/python --install-scripts /bin

cd $ROOT
/data/buildbot/buildbot.sh restart master
