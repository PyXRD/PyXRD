# coding=UTF-8
# ex:ts=4:sw=4:et=on
#  -------------------------------------------------------------------------
#  Copyright (C) 2014 by Mathijs Dumon <mathijs dot dumon at gmail dot com>
#
#  mvc is a framework derived from the original pygtkmvc framework
#  hosted at: <http://sourceforge.net/projects/pygtkmvc/>
#
#  mvc is free software; you can redistribute it and/or
#  modify it under the terms of the GNU Lesser General Public
#  License as published by the Free Software Foundation; either
#  version 2 of the License, or (at your option) any later version.
#
#  mvc is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#  Lesser General Public License for more details.
#
#  You should have received a copy of the GNU Lesser General Public
#  License along with this library; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor,
#  Boston, MA 02110, USA.
#  -------------------------------------------------------------------------

def run_dialog(dialog,
        on_accept_callback=None, on_reject_callback=None, destroy=True):
    """ Helper method - do not call directly """

    if not (on_accept_callback is None or callable(on_accept_callback)):
        raise ValueError("Accept callback must be None or callable")
    if not (on_reject_callback is None or callable(on_reject_callback)):
        raise ValueError("Reject callback must be None or callable")

    # Using an event prevents deadlocks, because we can return to the Main Loop
    def _dialog_response_cb(dialog, response):
        retval = None
        if response in dialog.accept_responses and on_accept_callback is not None:
            retval = on_accept_callback(dialog)
        elif on_reject_callback is not None:
            retval = on_reject_callback(dialog)
        if destroy:
            dialog.destroy()
        else:
            dialog.hide()
        return retval

    # Connect callback and present the dialog
    dialog.connect('response', _dialog_response_cb)
    dialog.set_modal(True)
    dialog.show()

def retrieve_lowercase_extension(glob):
    '''Ex: '*.[oO][rR][aA]' => '*.ora' '''
    return ''.join([ c.replace("[", "").replace("]", "")[:-1] for c in glob.split('][')])

def adjust_filename_to_globs(filename, globs):
    """ Adjusts a given filename so it ends with the proper extension """
    if globs: # If given use file extensions globs
        possible_fns = []
        # Loop over globs, if the current filenames extensions matches
        # a given glob, the filename is returned as is, otherwise
        # the extension of the first glob is added at the end of filename
        for glob in globs:
            if glob is not None:
                extension = glob[1:]
                if filename[len(filename) - len(extension):].lower() != extension.lower():
                    possible_fns.append("%s%s" % (filename, glob[1:]))
                else:
                    return filename # matching extension is returned immediately
        return possible_fns[0] # otherwise add extension of the first filter
    else: # If no globs are given, return filename as is
        return filename

