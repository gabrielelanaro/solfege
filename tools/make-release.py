#!/usr/bin/python
# vim: set fileencoding=utf-8:
import os
import re
import subprocess
import sys
import textwrap

# Set to True if we are building a devel release of a devel branch
# that are not actively translated.
not_translated = True

buildbranch = "build-branch"
print sys.argv, len(sys.argv[1].split("."))
if not (len(sys.argv) == 2 and len(sys.argv[1].split(".")) >= 3):
    print
    print "\n".join(textwrap.wrap("This script will make a branch of what we are working on now in %s/ make a release tarball in the current directory." % buildbranch))
    print
    print "USAGE: ./tools/make-release.py x.y.z"
    print "where x.y.z is the version number."
    sys.exit()
version_number = sys.argv[1]

def get_last_revision_id():
    p = subprocess.Popen(["bzr", "log", "-r", "-1", "--show-ids"],
        cwd=buildbranch,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT)
    while 1:
        p.poll()
        if p.returncode != None:
            break
        while True:
            s = p.stdout.readline()
            if s.startswith("revision-id:"):
                retval = s.split()[1]
                break
            if not s:
                break
    p.wait()
    return retval

class Logger(object):
    def __init__(self, filename):
        self.logfile = open(filename, 'w')
        self.close = self.logfile.close
    def call(self, *args, **kwargs):
        kwargs['stdout'] = subprocess.PIPE
        kwargs['stderr'] = subprocess.STDOUT
        p = subprocess.Popen(*args, **kwargs)
        while 1:
            p.poll()
            if p.returncode != None:
                break
            while True:
                s = p.stdout.readline()
                print s.strip()
                self.logfile.write(s)
                if not s:
                    break
        p.wait()
        if p.returncode != 0:
            print "p.returncode =", p.returncode
            sys.exit()
        return p.returncode
    
def update_configure_ac(new_revid, version):
    f = open(os.path.join(buildbranch, "configure.ac"), "r")
    s = f.read()
    f.close()
    m = re.search("REVISION_ID=\"(.*?)\"", s)
    s = s[:m.start()+len("REVISION_ID=\"")] + new_revid + s[m.end()-1:]
    m = re.search("MAJOR_VERSION=.*?$", s, re.MULTILINE)
    s = s[:m.start()+len("MAJOR_VERSION=")] + version.split(".")[0] + s[m.end():]
    m = re.search("MINOR_VERSION=.*?$", s, re.MULTILINE)
    s = s[:m.start()+len("MINOR_VERSION=")] + version.split(".")[1] + s[m.end():]
    m = re.search("PATCH_LEVEL=.*?$", s, re.MULTILINE)
    s = s[:m.start()+len("PATCH_LEVEL=")] + ".".join(version.split(".")[2:]) + s[m.end():]

    m = re.search("AC_INIT\(\[GNU Solfege\],\[.*?\]", s, re.MULTILINE)
    s = s[:m.start()+len("AC_INIT([GNU Solfege],[")] + version + s[m.end()-1:]

    f = open(os.path.join(buildbranch, "configure.ac"), "w")
    f.write(s)
    f.close()


bl = Logger("build.log")
if not not_translated:
    bl.call(["make", "check-for-new-po-files"])
    bl.call(["make", "check-for-new-manual-po-files"])

if os.path.exists(buildbranch):
    print "«%s» exists" % buildbranch
    sys.exit(1)
bl.call(["bzr", "branch", ".", buildbranch])
update_configure_ac(get_last_revision_id(), version_number)
bl.call(["./autogen.sh"], cwd=buildbranch)
bl.call(["make"], cwd=buildbranch)
if not_translated:
    bl.call(["make", "update-manual"], cwd=buildbranch)
    bl.call(["make", "check-revision-id"], cwd=buildbranch)
    bl.call(["make", "test"], cwd=buildbranch)
else:
    bl.call(["make", "prepare-release"], cwd=buildbranch)
bl.call(["make", "dist"], cwd=buildbranch)
bl.close()
