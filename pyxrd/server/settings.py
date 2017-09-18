
import Pyro4
Pyro4.config.SERIALIZERS_ACCEPTED = ["json", "marshal", "serpent", "pickle"]
Pyro4.config.SERIALIZER = "pickle"
Pyro4.config.COMPRESSION = True
Pyro4.config.SERVERTYPE = "multiplex"
Pyro4.config.COMMTIMEOUT = 3.5
Pyro4.config.REQUIRE_EXPOSE = False
Pyro4.config.SOCK_REUSE = True

import platform
if platform.system() == "Windows" and float(platform.release()) >= 6:
    USE_MSG_WAITALL = True

PYRO_NAME = "pyxrd.server"
KEEP_SERVER_ALIVE = False # setting this to false may produce unwanted results!