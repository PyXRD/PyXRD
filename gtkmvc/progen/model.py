#  Author: Roberto Cavada <roboogle@gmail.com>
#
#  Copyright (c) 2007 by Roberto Cavada
#
#  pygtkmvc is free software; you can redistribute it and/or
#  modify it under the terms of the GNU Lesser General Public
#  License as published by the Free Software Foundation; either
#  version 2 of the License, or (at your option) any later version.
#
#  pygtkmvc is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#  Lesser General Public License for more details.
#
#  You should have received a copy of the GNU Lesser General Public
#  License along with this library; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor,
#  Boston, MA 02110, USA.
#
#  For more information on pygtkmvc see <http://pygtkmvc.sourceforge.net>
#  or email to the author Roberto Cavada <roboogle@gmail.com>.
#  Please report bugs to <roboogle@gmail.com>.


import os
import glob
import datetime
import shutil
from string import Template

from gtkmvc import Model
from gtkmvc.progen import templates
# relpath is taken from utils here for portability
from gtkmvc.support.utils import relpath

# ----------------------------------------------------------------------
# Logging stuff
_log = None
__gui_buf = None

def __shell_log(msg):
    print msg
    return

def __gui_log(msg):
    __gui_buf.insert(__gui_buf.get_end_iter(), msg+"\n")
    return

def set_gui_log(buf):
    global __gui_buf, _log

    assert __gui_buf is None
    __gui_buf = buf
    _log = __gui_log
    buf.set_text("")
    return

def set_shell_log():
    global __gui_buf, _log

    __gui_buf = None
    _log = __shell_log
    return
# ----------------------------------------------------------------------


class ProgenModel (Model):
    """The application model"""
    name  = "" 
    glade = True
    glade_fn = "application.glade"
    author = ""
    email     = ""
    copyright = ""
    destdir = "."
    complex = True
    src_header = None
    other_comment = ""
    src_name      = "src"
    res_name      = "resources"
    top_widget    = "window_appl"
    dist_gtkmvc = True 

    __observables__ = ("name", "glade", "glade_fn", "author", 
                       "email", "copyright", "destdir", "complex", 
                       "src_header", "other_comment", "src_name", 
                       "res_name", "top_widget", "dist_gtkmvc",
                       )


    def __init__(self):
        Model.__init__(self)

        self.__own_copyright = True
        self.__itsme = False
        self.templ = templates.DEFAULT_MAP.copy()

        self.register_observer(self)
        return

    def generate_project(self):
        """
        Generate the whole project. Returns True if at least one
        file has been generated, False otherwise."""
        # checks needed properties
        if not self.name or not self.destdir or \
               not os.path.isdir(self.destdir):
            raise ValueError("Empty or invalid property values")

        _log("Generating project '%s'" % self.name)
        _log("Destination directory is: '%s'" % self.destdir)
        
        top = os.path.join(self.destdir, self.name)
        src = os.path.join(top, self.src_name)
        resources = os.path.join(top, self.res_name)
        utils = os.path.join(src, "utils")
        
        if self.complex:
            models = os.path.join(src, "models")
            ctrls = os.path.join(src, "ctrls")
            views = os.path.join(src, "views")            
        else: models = ctrls = views = src 

        res = self.__generate_tree(top, src, resources, models, ctrls, views, utils)
        res = self.__generate_classes(models, ctrls, views) or res
        res = self.__mksrc(os.path.join(utils, "globals.py"), templates.glob) or res

        if self.complex: self.templ.update({'model_import' : "from models.application import ApplModel",
                                            'ctrl_import' : "from ctrls.application import ApplCtrl",
                                            'view_import' : "from views.application import ApplView"})
        else: self.templ.update({'model_import' : "from ApplModel import ApplModel",
                                 'ctrl_import' : "from ApplCtrl import ApplCtrl",
                                 'view_import' : "from ApplView import ApplView"})            
        
        res = self.__mksrc(os.path.join(top, "%s.py" % self.name), templates.main) or res

        # glade file
        if self.glade: res = self.__generate_glade(resources) or res

        if self.dist_gtkmvc: res = self.__copy_framework(os.path.join(resources, "external")) or res

        if not res: _log("No actions were taken")
        else: _log("Done")
        return res
    

    def __generate_tree(self, top, src, resources, models, ctrls, views, utils):
        """Creates directories and packages"""
        res = self.__mkdir(top)
        for fn in (src, models, ctrls, views, utils): res = self.__mkpkg(fn) or res
        res = self.__mkdir(resources) or res
        res = self.__mkdir(os.path.join(resources, "glade")) or res
        res = self.__mkdir(os.path.join(resources, "styles")) or res
        res = self.__mkdir(os.path.join(resources, "external")) or res
        return res

    def __generate_classes(self, models, ctrls, views):
        # model
        src = self.__generate_class_template("Model", "ApplModel", templates.model)
        if self.complex: name = "application.py"
        else: name = "ApplModel.py"
        res = self.__mksrc(os.path.join(models, name), src)

        # controller
        src = self.__generate_class_template("Controller", "ApplCtrl", templates.ctrl)
        if self.complex: name = "application.py"
        else: name = "ApplCtrl.py"
        res = self.__mksrc(os.path.join(ctrls, name), src) or res
        
        # view
        if self.glade: src = self.__generate_class_template("View", "ApplView", templates.view_glade)
        else: src = self.__generate_class_template("View", "ApplView", templates.view_noglade)

        if self.complex: name = "application.py"
        else: name = "ApplView.py"
        res = self.__mksrc(os.path.join(views, name), src) or res
        return res

    def __generate_glade(self, resources):
        fn = os.path.join(os.path.join(os.path.join(resources, "glade"),
                                       self.glade_fn))
        if os.path.isfile(fn): return False
        
        _log("Creating glade file %s" % fn)
        f = open(fn, "w")
        f.write(Template(templates.glade_file).safe_substitute(self.templ))
        f.close()
        return True


    def __generate_class_template(self, base, name, template):
        return Template(template).safe_substitute({'base_class_name' : base,
                                                   'class_name' : name,
                                                   })

    def __copy_framework(self, destdir):
        # copies gtkmvc packages, creating a zip package
        if not os.path.isdir(destdir): return False

        from gtkmvc.progen.globals import GTKMVC_DIR
        if GTKMVC_DIR is None:
            _log("Warning: the gtkmvc framework was not found")
            return False

        _log("The gtkmvc framework was found in '%s'" % GTKMVC_DIR)

        # creates destdir
        if not os.path.isdir(destdir):
            _log("Creating directory '%s'" % destdir)
            os.makedirs(destdir)
            pass
        
        # copies the source files
        gtkmvc_parent = os.path.dirname(GTKMVC_DIR)
        for root, dirs, files in os.walk(GTKMVC_DIR):
            if ".svn" in dirs: dirs.remove(".svn")
            if "progen" in dirs: dirs.remove("progen")

            relroot = relpath(root, gtkmvc_parent)
            pyfiles = glob.glob(os.path.join(root, "*.py"))
            if pyfiles:
                _dest = os.path.join(destdir, relroot)
                if not os.path.isdir(_dest):
                    _log("Creating directory '%s'" % _dest)
                    os.mkdir(_dest)
                    pass

                for py in pyfiles:
                    pydest = os.path.join(_dest, relpath(py, root))
                    if not os.path.isfile(pydest):
                        _log("Copying file '%s' into '%s'" % (py, pydest))
                        shutil.copy(py, pydest)
                        pass
                    pass
                pass
            pass
        
        # copies non-source files
        for relsrc, reldest in (("gtkmvc/progen/README.txt", "gtkmvc/README.txt"),):
            _dest = os.path.join(destdir, reldest)
            _dest_dir = os.path.dirname(_dest)

            if not os.path.isdir(_dest_dir):
                _log("Creating directory '%s'" % _dest_dir)
                os.makedirs(_dest_dir)
                pass
            
            if not os.path.isfile(_dest):
                _src = os.path.join(gtkmvc_parent, relsrc)
                _log("Copying file '%s' into '%s'" % (_src, _dest))
                shutil.copy(_src, _dest)
                pass
            pass
        
        _log("Copied the gtkmvc framework into %s" % destdir)
        return True
    
        
    # Services
    def __mkdir(self, path):
        if os.path.isdir(path): return False
        _log("Creating directory '%s'" % path)
        os.makedirs(path)
        return True
                             
    def __mkpkg(self, path):
        res = self.__mkdir(path)
        res = self.__mksrc(os.path.join(path, "__init__.py")) or res
        return res

    def __get_source(self, path, template=""):
        m = { 'filename'  : os.path.basename(path),
              'directory' : os.path.dirname(path),
              'comment'   : self.other_comment,
              'date'      : datetime.datetime.today().ctime(),
              }

        for k in self.__observables__: m[k] = getattr(self, k)
        self.templ.update(m)
        
        if self.src_header is None: header = templates.DEFAULT_HEADER + template
        else: header = self.src_header + "\n\n$comment\n" + template
        return Template(header).safe_substitute(self.templ)

    def __mksrc(self, path, template=""):
        if os.path.isfile(path): return False
        _log("Creating source file '%s'" % path)
        
        f = open(path, "w")
        f.write(self.__get_source(path, template))
        f.close()
        return True
        
    # some code to generate a default string for copyright
    @Model.observe("author", assign=True)
    def author_change(self, model, pname, info):
        if self.__own_copyright:
            self.__itsme = True
            if info.new in ("", None): self.copyright = ""
            else:
                self.copyright = "Copyright (C) %d by %s" \
                    % (datetime.datetime.today().year, info.new)
                pass
            self.__itsme = False
            pass
        return

    @Model.observe("copyright", assign=True)
    def copyright_change(self, model, pname, info):
        if self.__itsme: return
        self.__own_copyright = info.new in ("",None)
        return

    
    pass # end of class
