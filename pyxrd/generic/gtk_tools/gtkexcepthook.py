# (c) 2003 Gustavo J A M Carneiro gjc at inescporto.pt
#     2004-2005 Filip Van Raemdonck
#
# http://www.daa.com.au/pipermail/pygtk/2003-August/005775.html
# Message-ID: <1062087716.1196.5.camel@emperor.homelinux.net>
#     "The license is whatever you want."
#
# This file was downloaded from http://www.sysfs.be/downloads/
# Adaptions 2009-2010 by Martin Renold:
# - let KeyboardInterrupt through
# - print traceback to stderr before showing the dialog
# - nonzero exit code when hitting the "quit" button
# - suppress more dialogs while one is already active
# - fix Details button when a context in the traceback is None
# - remove email features
# - fix lockup with dialog.run(), return to mainloop instead
# see also http://faq.pygtk.org/index.py?req=show&file=faq20.010.htp
# Changes 2012 by Mathijs Dumon:
# - removed the gtkcompat import statement

import inspect, linecache, pydoc, sys, traceback
from cStringIO import StringIO
from gettext import gettext as _

import gtk
import pango

original_excepthook = sys.excepthook

class GtkExceptionHook():
    """
        Exception handling GTK-dialog hook 
    """

    # Function that will be called when the user presses "Quit"
    # Return True to confirm quit, False to cancel
    quit_confirmation_func = None

    exception_dialog_active = False

    RESPONSE_QUIT = 1

    def analyze_simple (self, exctyp, value, tb):
        """
            Analyzes the exception into a human readable stack trace
        """
        trace = StringIO()
        traceback.print_exception (exctyp, value, tb, None, trace)
        return trace

    def lookup (self, name, frame, lcls):
        '''Find the value for a given name in the given frame'''
        if name in lcls:
            return 'local', lcls[name]
        elif name in frame.f_globals:
            return 'global', frame.f_globals[name]
        elif '__builtins__' in frame.f_globals:
            builtins = frame.f_globals['__builtins__']
            if type (builtins) is dict:
                if name in builtins:
                    return 'builtin', builtins[name]
            else:
                if hasattr (builtins, name):
                    return 'builtin', getattr (builtins, name)
        return None, []

    _parent_window = [None]
    _level = 0
    @property
    def parent_window(self):
        return self._parent_window[self._level]
    @parent_window.setter
    def parent_window(self, value):
        self._parent_window[self._level] = value

    def overriden_parent_window(self, parent):
        """
            Sets the parent window temporarily to another value
            and returns itself, so this can be used as a context
            manager.
        """
        self._parent_window.append(parent)
        self._level = len(self._parent_window)
        return self

    def __enter__(self):
        pass

    def __exit__(self):
        if self._level > 0:
            self._parent_window.pop(self._level)
            self._level = len(self._parent_window)

    def analyze (self, exctyp, value, tb):
        """
            Analyzes the exception into a human readable stack trace
        """
        import tokenize, keyword

        trace = StringIO()
        nlines = 3
        frecs = inspect.getinnerframes (tb, nlines)
        trace.write ('Traceback (most recent call last):\n')
        for frame, fname, lineno, funcname, context, cindex in frecs:
            trace.write ('  File "%s", line %d, ' % (fname, lineno))
            args, varargs, varkw, lcls = inspect.getargvalues (frame)

            def readline (lno=[lineno], *args):
                if args: print args
                try: return linecache.getline (fname, lno[0])
                finally: lno[0] += 1
            all, prev, name, scope = {}, None, '', None
            for ttype, tstr, stup, etup, line in tokenize.generate_tokens (readline):
                if ttype == tokenize.NAME and tstr not in keyword.kwlist:
                    if name:
                        if name[-1] == '.':
                            try:
                                val = getattr (prev, tstr)
                            except AttributeError:
                                # XXX skip the rest of this identifier only
                                break
                            name += tstr
                    else:
                        assert not name and not scope
                        scope, val = self.lookup(tstr, frame, lcls)
                        name = tstr
                    if val is not None:
                        prev = val
                elif tstr == '.':
                    if prev:
                        name += '.'
                else:
                    if name:
                        all[name] = (scope, prev)
                    prev, name, scope = None, '', None
                    if ttype == tokenize.NEWLINE:
                        break

            try:
                details = inspect.formatargvalues (args, varargs, varkw, lcls, formatvalue=lambda v: '=' + pydoc.text.repr (v))
            except:
                # seen that one on Windows (actual exception was KeyError: self)
                details = '(no details)'
            trace.write (funcname + details + '\n')
            if context is None:
                context = ['<source context missing>\n']
            trace.write (''.join (['    ' + x.replace ('\t', '  ') for x in filter (lambda a: a.strip(), context)]))
            if len (all):
                trace.write ('  variables: %s\n' % str (all))

        trace.write ('%s: %s' % (exctyp.__name__, value))
        return trace

    def __call__ (self, exctyp, value, tb):
        """
            This is called when an exception occurs.
        """
        if exctyp is KeyboardInterrupt:
            return original_excepthook(exctyp, value, tb)
        sys.stderr.write(self.analyze_simple (exctyp, value, tb).getvalue())
        if self.exception_dialog_active:
            return

        gtk.gdk.pointer_ungrab(gtk.gdk.CURRENT_TIME)
        gtk.gdk.keyboard_ungrab(gtk.gdk.CURRENT_TIME)

        self.exception_dialog_active = True
        # Create the dialog
        dialog = gtk.MessageDialog(
            parent=self.parent_window,
            flags=0, type=gtk.MESSAGE_WARNING, buttons=gtk.BUTTONS_NONE
        )
        dialog.set_title (_("Bug Detected"))

        primary = _("<big><b>A programming error has been detected.</b></big>")
        secondary = _("It probably isn't fatal, but the details should be reported to the developers nonetheless.")

        try:
            setsec = dialog.format_secondary_text
        except AttributeError:
            raise
            dialog.vbox.get_children()[0].get_children()[1].set_markup ('%s\n\n%s' % (primary, secondary))
        else:
            del setsec
            dialog.set_markup (primary)
            dialog.format_secondary_text (secondary)

        dialog.add_button (gtk.STOCK_CLOSE, gtk.RESPONSE_CLOSE)
        dialog.add_button (gtk.STOCK_QUIT, self.RESPONSE_QUIT)

        # Add an expander with details of the problem to the dialog
        def expander_cb(expander, *ignore):
            # Ensures that on deactivating the expander, the dialog is resized down
            if expander.get_expanded():
                dialog.set_resizable(True)
            else:
                dialog.set_resizable(False)
        details_expander = gtk.Expander()
        details_expander.set_label(_("Details..."))
        details_expander.connect("notify::expanded", expander_cb)

        textview = gtk.TextView(); textview.show()
        textview.set_editable (False)
        textview.modify_font (pango.FontDescription ("Monospace"))

        sw = gtk.ScrolledWindow(); sw.show()
        sw.set_policy (gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        sw.set_size_request(800, 400)
        sw.add (textview)

        details_expander.add (sw)
        details_expander.show_all()
        dialog.get_content_area().pack_start(details_expander)

        # Get the traceback and set contents of the details
        try:
            trace = self.analyze(exctyp, value, tb).getvalue()
        except:
            try:
                trace = _("Exception while analyzing the exception.") + "\n"
                trace += analyse_simple (exctyp, value, tb).getvalue()
            except:
                trace = _("Exception while analyzing the exception.")
        buf = textview.get_buffer()
        buf.set_text (trace)

        # Connect callback and present the dialog
        dialog.connect('response', self._dialog_response_cb, trace)
        dialog.set_modal(True)
        dialog.show()
        dialog.present()


    def _dialog_response_cb(self, dialog, resp, trace):

        if resp == self.RESPONSE_QUIT and gtk.main_level() > 0:
            if not callable(self.quit_confirmation_func):
                sys.exit(1) # Exit code is important for IDEs
            else:
                if self.quit_confirmation_func():
                    sys.exit(1) # Exit code is important for IDEs
                else:
                    dialog.destroy()
                    self.exception_dialog_active = False

        else:
            dialog.destroy()
            self.exception_dialog_active = False

def plugin_gtk_exception_hook():
    hook = GtkExceptionHook()
    sys.excepthook = hook
    return hook
