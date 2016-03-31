#!/bin/python

import sys, os
import subprocess
import re
import fileinput

def update_version(filename, version):
    for line in fileinput.input(filename, inplace=True):
        rexp = "__version__\s*=.*"
        line = re.sub(rexp, "__version__ = \"%s\"" % version, line),
        print line[0],

assert len(sys.argv) > 1, "You need to specify the version (e.g. 6.6.6)"
assert "v" not in sys.argv[1], "You need to the version (e.g. 6.6.6)"

update_version(os.path.abspath("pyxrd/__version.py"), sys.argv[1])
update_version(os.path.abspath("mvc/__version.py"), sys.argv[1])

print subprocess.check_output(['git', 'add', 'pyxrd/__version.py'])
print subprocess.check_output(['git', 'add', 'mvc/__version.py'])
print subprocess.check_output(['git', 'commit', '-m', 'Version bump', '--allow-empty'])
print subprocess.check_output(['git', 'tag', '-a', 'v%s' % sys.argv[1], '-m', 'v%s' % sys.argv[1]])
