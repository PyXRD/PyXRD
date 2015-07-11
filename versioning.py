#!/usr/bin/env python

""" Git Versioning Script

Will transform stdin to expand some keywords with git version/author/date information.

Specify --clean to remove this information before commit.

Setup:

1. Copy versioning.py into your git repository

2. Run:

 git config filter.versioning.smudge 'python versioning.py'
 git config filter.versioning.clean  'python versioning.py --clean'
 echo 'version.py filter=versioning' >> .gitattributes
 git add versioning.py


3. add a version.py file with this contents:

 __version__ = ""

"""

import sys
import subprocess
import re


def main():
    clean = False
    if len(sys.argv) > 1:
        if sys.argv[1] == '--clean':
            clean = True

    # initialise empty here. Otherwise: forkbomb through the git calls.
    subst_list = {
        "version": "",
    }

    for line in sys.stdin:
        if not clean:
            subst_list = {
                # '--dirty' could be added to the following, too, but is not supported everywhere
                "version": subprocess.check_output(['git', 'describe', '--always']),
            }
            for k, v in subst_list.iteritems():
                v = re.sub(r'[\n\r\t"\']', "", v)
                rexp = "__%s__\s*=[\s'\"]+" % k
                line = re.sub(rexp, "__%s__ = \"%s\"\n" % (k, v), line)
            sys.stdout.write(line)
        else:
            for k in subst_list:
                rexp = "__%s__\s*=.*" % k
                line = re.sub(rexp, "__%s__ = \"\"" % k, line)
            sys.stdout.write(line)


if __name__ == "__main__":
    main()
