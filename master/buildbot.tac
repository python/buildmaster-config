
from twisted.application import service
from buildbot.master import BuildMaster

basedir = r'/data/buildbot/master'
configfile = r'master.cfg'
maxRotatedFiles = 100

application = service.Application('buildmaster')
BuildMaster(basedir, configfile).setServiceParent(application)

