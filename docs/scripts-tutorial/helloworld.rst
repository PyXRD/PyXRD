Hello World script
==================

Fire up your favorite text editor and copy the following piece of code:

.. code-block:: python
   
   #!/usr/bin/python
   # coding=UTF-8
   
   import logging
   logger = logging.getLogger(__name__)
   
   def run(args):
       """
           Run as
            python core.py -s path/to/hello_world.py
       """
       logging.info("Creating a new project")
       
       from pyxrd.project.models import Project
       project = Project(name="Hello World", description="This is a hello world project")
   
       from pyxrd.scripts.tools import reload_settings, launch_gui
       reload_settings()
       launch_gui(project)     # from this point onwards, the GUI takes over!

What this script does is very simple: it will create a new project, with it's
name and title set to "Hello World" and "This is a hello world project" 
respectively. Then it will launch the gui as it would normally start but pass in
this newly created project. What you should see is PyXRD loading as usual but
with this new project pre-loaded. 

Running the script
==================

Save the script somewhere (e.g. on your desktop) and name it "hello_world.py".

To run this script you have to tell PyXRD where to find it first. So instead
of starting PyXRD as you would usually do, open up a command line (Windows) or
terminal (Linux), and follow the instructions below.
 
Windows
-------
On windows the following command should start PyXRD with the script:

.. code-block:: bat

   C:\Python27\Scripts\PyXRD.exe -s "C:\path\to\script\hello_world.py"
  
Replace the path\\to\\script part with the actual path where you saved the script.
The above example also assumes you have installed python in C:\\Python27 (the default).

Linux
-----
On linux the following command should start PyXRD with the script:

.. code-block:: bash

   PyXRD -s "/path/to/script/hello_world.py"'
   
Replace the /path/to/script/ part with the actual path where you saved the script.
This assumes you have installed PyXRD using pip so that the PyXRD command is
picked up by the terminal. If you get an error like 'PyXRD: command not found',
you will need to find out where PyXRD was installed and use the full path instead.

