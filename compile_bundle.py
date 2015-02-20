import fileinput
from subprocess import check_call
from pyxrd import __version__

from shutil import copyfile

copyfile("PyXRDiss.iss", "PyXRD.iss")

for line in fileinput.input("PyXRD.iss", inplace=True):
    line = line.replace('|||VERSION|||', __version__)
    print "%s" % (line),
