#!/usr/bin/env python
# -*- coding: utf-8; mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vim: fileencoding=utf-8 tabstop=4 expandtab shiftwidth=4

# (C) COPYRIGHT © Preston Landers 2010, © Mathijs Dumon 2014
# Released under the same license as Python 2.6.5

import sys, os, traceback, types, base64, tempfile
import urllib, subprocess
from Tkinter import *
import ttk
import time
import threading

base_text = "Installing dependencies and PyXRD, this may take a while ..."

def __install_hub(installers, root, label):
    for title, urlpos, command, url in installers:
        if url != "":
            print "Downloading %s from %s ..." % (title, url)
            def hook(count, block_size, total_size):
                if total_size > 0:
                    progress = (100 * count * block_size / total_size)
                    progress = "%d %%" % progress
                else:
                    progress = "? %"
                label.set(base_text + "\nDownloading %s %s" % (title, progress))
            label.set(base_text + "\nDownloading %s ..." % title)
            try:
                fname, headers = urllib.urlretrieve(url, reporthook=hook)
            except IOError:
                #Try again:
                fname, headers = urllib.urlretrieve(url, reporthook=hook)
        else:
            fname = url
        
        print "Installing %s ..." % title
        label.set(base_text + "\nInstalling %s ..." % title)
        if urlpos == -1:
            command.append(fname)
        else:
            command.insert(urlpos, fname)

        subprocess.call(command)

def install_others(root, label):
    installers = [
       ("Setuptools", -1, [r"C:\Python27\python.exe",], r"https://bootstrap.pypa.io/ez_setup.py"),
       ("Pip",        -1, [r"C:\Python27\Scripts\easy_install.exe", "pip"], ""),
       ("win32api",   -1, [r"C:\Python27\Scripts\easy_install.exe",], "http://downloads.sourceforge.net/projects/pywin32/pywin32/Build%20219/pywin32-219.win32-py2.7.exe"),
       ("win32api",   -1, [r"C:\Python27\python.exe", r"C:\Python27\Scripts\pywin32_postinstall.py", r"-install"], ""),
       ("PyGTK",       2, [r"msiexec", r"/i", r"/passive", r"ALLUSERS=1", r'TARGETDIR="C:\Python27"'], r"http://ftp.gnome.org/pub/GNOME/binaries/win32/pygtk/2.24/pygtk-all-in-one-2.24.2.win32-py2.7.msi"),
       ("Numpy",      -1, [], r"http://sourceforge.net/projects/numpy/files/NumPy/1.7.0/numpy-1.7.0-win32-superpack-python2.7.exe/download"),
       ("Scipy",      -1, [], r"http://sourceforge.net/projects/scipy/files/scipy/0.14.0/scipy-0.14.0-win32-superpack-python2.7.exe/download"),
       ("Pyparsing",  -1, [r"C:\Python27\Scripts\easy_install.exe",], r"https://pypi.python.org/packages/any/p/pyparsing/pyparsing-2.0.3.win32-py2.7.exe#md5=1ca37c237b92ae033feec47cc00b7d14"),
       ("Matplotlib", -1, [r"C:\Python27\Scripts\easy_install.exe",], r"https://downloads.sourceforge.net/projects/matplotlib/matplotlib/matplotlib-1.2.1/matplotlib-1.2.1.win32-py2.7.exe"),
       ("PyXRD",      -1, [r"C:\Python27\Scripts\easy_install.exe",], r"https://pypi.python.org/packages/any/P/PyXRD/PyXRD-0.6.2.win32-py2.7.exe"),
       ("PyXRD",      -1, [r"C:\Python27\python.exe", r"C:\Python27\Scripts\win32_pyxrd_post_install.py -install"], ""),
    ]

    __install_hub(installers, root, label)

    root.destroy()

def create_progress_bar(root):
    #Set the icon on the window:
    icon = icon='''\
AAABAAIAEBAAAAAAIABoBAAAJgAAACAgAAAAACAAqBAAAI4EAAAoAAAAEAAAACAAAAABACAAAAAA
AEAEAAAAAAAAAAAAAAAAAAAAAAAA////Af///wH///8B////Af///wH///8B////Af///wH///8B
////Af///wH///8B////Af///wH///8B////Af///wH///8B////Af///wH///8B////Af///wH/
//8B////Af///wH///8B////Af///wH///8B////Af///wH///8B////Af///wH///8B////Af//
/wH///8B////Af///wH///8B////Af///wH///8B////Af///wH///8B////Af///wH///8B////
Af///wH///8B////Af///wH///8B////Af///wH///8B////Af///wH///8B////AQAAABUAAABB
AAAAQQAAAEEAAABBAAAAQQAAAEEAAABBAAAAQQAAAEEAAABBAAAAQQAAAEEAAABBAAAAQQAAABUA
AAALAAAAIQAAACFMTExLSUlJVQAAACEAAAAhAAAAIQAAACEAAAAhAAAAIQAAACEAAAAhAAAAIQAA
ACEAAAALeHh4O4aGhiv///8Bk5OTITw8PNO7u7sjd3d3Yf///wN6enpjdHR0VZmZmR1nZ2dXiIiI
WVFRUWV0dHRD////ATk5OYlQUFCRlZWVK35+fjMxMTHlUFBQaT4+PpdKSkq/Q0NDjysrK7tzc3OD
OTk5zTo6OpVSUlKRKSkpyWFhYVc5OTmJR0dHmS4uLt9RUVGtg4ODWUdHR8VsbGxNFhYW935+fkUr
Kyu7UlJSqUZGRq82NjaTWlpaW0JCQotFRUV3VlZWeVBQUMFJSUmp39/fF////wHg4OAbU1NTu42N
jUtYWFi5TExMp1hYWL1GRkaHU1NTf01NTcM4ODixkJCQGwAAAAsAAAAhAAAAIQAAACEAAAAhAAAA
IQAAACEAAAAhAAAAIQAAACEAAAAhAAAAIQAAACEAAAAhAAAAIQAAAAsAAAAVAAAAQQAAAEEAAABB
AAAAQQAAAEEAAABBAAAAQQAAAEEAAABBAAAAQQAAAEEAAABBAAAAQQAAAEEAAAAV////Af///wH/
//8B////Af///wH///8B////Af///wH///8B////Af///wH///8B////Af///wH///8B////Af//
/wH///8B////Af///wH///8B////Af///wH///8B////Af///wH///8B////Af///wH///8B////
Af///wH///8B////Af///wH///8B////Af///wH///8B////Af///wH///8B////Af///wH///8B
////Af///wH///8B////Af///wH///8B////Af///wH///8B////Af///wH///8B////Af///wH/
//8B////Af///wH///8B////AQAA//8AAP//AAD//wAA//8AAP//AAD//wAA//8AAP//AAD//wAA
//8AAP//AAD//wAA//8AAP//AAD//wAA//8oAAAAIAAAAEAAAAABACAAAAAAAIAQAAAAAAAAAAAA
AAAAAAAAAAAA////Af///wH///8B////Af///wH///8B////Af///wH///8B////Af///wH///8B
////Af///wH///8B////Af///wH///8B////Af///wH///8B////Af///wH///8B////Af///wH/
//8B////Af///wH///8B////Af///wH///8B////Af///wH///8B////Af///wH///8B////Af//
/wH///8B////Af///wH///8B////Af///wH///8B////Af///wH///8B////Af///wH///8B////
Af///wH///8B////Af///wH///8B////Af///wH///8B////Af///wH///8B////Af///wH///8B
////Af///wH///8B////Af///wH///8B////Af///wH///8B////Af///wH///8B////Af///wH/
//8B////Af///wH///8B////Af///wH///8B////Af///wH///8B////Af///wH///8B////Af//
/wH///8B////Af///wH///8B////Af///wH///8B////Af///wH///8B////Af///wH///8B////
Af///wH///8B////Af///wH///8B////Af///wH///8B////Af///wH///8B////Af///wH///8B
////Af///wH///8B////Af///wH///8B////Af///wH///8B////Af///wH///8B////Af///wH/
//8B////Af///wH///8B////Af///wH///8B////Af///wH///8B////Af///wH///8B////Af//
/wH///8B////Af///wH///8B////Af///wH///8B////Af///wH///8B////Af///wH///8B////
Af///wH///8B////Af///wH///8B////Af///wH///8B////Af///wH///8B////Af///wH///8B
////Af///wH///8B////Af///wH///8B////Af///wH///8B////Af///wH///8B////Af///wH/
//8B////Af///wH///8B////Af///wH///8B////Af///wH///8B////Af///wH///8B////Af//
/wH///8B////Af///wH///8B////Af///wH///8B////Af///wH///8B////Af///wH///8B////
Af///wH///8B////Af///wH///8B////Af///wH///8B////Af///wH///8B////Af///wH///8B
////Af///wH///8B////Af///wH///8B////Af///wH///8B////Af///wH///8B////Af///wH/
//8B////Af///wH///8B////Af///wH///8B////Af///wH///8B////Af///wH///8B////Af//
/wH///8B////Af///wH///8B////Af///wH///8B////Af///wH///8B////Af///wH///8B////
Af///wH///8B////Af///wH///8B////AQAAAFEAAACBAAAAgQAAAIEAAACBAAAAgQAAAIEAAACB
AAAAgQAAAIEAAACBAAAAgQAAAIEAAACBAAAAgQAAAIEAAACBAAAAgQAAAIEAAACBAAAAgQAAAIEA
AACBAAAAgQAAAIEAAACBAAAAgQAAAIEAAACBAAAAUf///wH///8BAAAAKQAAAEEAAABBAAAAQQAA
AEEAAABBAAAAQQAAAEEAAABBAAAAQQAAAEEAAABBAAAAQQAAAEEAAABBAAAAQQAAAEEAAABBAAAA
QQAAAEEAAABBAAAAQQAAAEEAAABBAAAAQQAAAEEAAABBAAAAQQAAAEEAAAAp////Af///wH///8B
////Af///wH///8B////Af///wGGhoarZmZmoaqqqjP///8B////Af///wH///8B////Af///wH/
//8B////Af///wH///8B////Af///wH///8B////Af///wH///8B////Af///wH///8B////Af//
/wH///8B////Af///wH///8B////Af///wH///8B////AZOTk4NDQ0PXXFxcwf///wP///8B////
Af///wH///8B////Af///wH///8B////Af///wH///8B////Af///wH///8B////Af///wH///8B
////Af///wH///8B////Af///wH///8Xampq04aGhqv///8B////Af///wH///8B////AVpaWrMK
Cgr/ra2tVdHR0TN0dHTPfHx8s////wX///8JdHR0vYCAgMuzs7N/Tk5O0ZmZmXP///8Bi4uLjVBQ
UNHGxsaLYWFh1U9PT89VVVXBYGBgrZubm13///8B////Af///xknJyf7V1dXvf///wH///8B////
Af///wG0tLQzHBwc9xwcHPtnZ2el////AX5+fpEHBwf/kpKSiYWFhZUHBwf/jo6Of4iIiHkAAAD/
gYGBf9PT0x03NzfpRUVF3fDw8DMcHBz/QkJC2V5eXrU1NTXtDQ0N/YeHh33///8B////GScnJ/s8
PDzfZGRkpYWFhX3Dw8Mv////AW1tbZslJSXzgYGBsTQ0NOnm5uYV////B1BQUMkrKyvvHh4e82Nj
Y7n///8DiIiIeQAAAP94eHi1WFhYvwwMDP2Pj49z6+vrJxwcHP9aWlq1////Abq6ukMVFRX7TExM
3f///wH///8ZJycn+zExMedUVFTDGxsb80dHR9/Y2NgbODg46V1dXa+oqKhVBgYG/4qKinf///8B
n5+fZQQEBP8ODg7/u7u7U////wGIiIh5AAAA/zw8POcvLy/xVVVV26ampjnr6+snHBwc/1paWrX/
//8B////AU5OTtkwMDD1////Ef///xknJyf7V1dXvf///wFnZ2epBQUF/6qqqrUbGxv/o6OjX///
/wVRUVHdaGhoxf///wdOTk7HKysr7x4eHvNiYmK7////A4iIiHkAAAD/gYGBf7m5uU0LCwv/b29v
qevr6yccHBz/Wlpatf///wG6urpZDg4O/VFRUdf///8B////GScnJ/s5OTnhXFxcsSQkJO06Ojrl
4eHhK97e3i////8D////AeHh4SPi4uIte3t7jQYGBv+Pj4+HhYWFlQcHB/+KioqBiIiIeQAAAP9Z
WVnJU1NTywAAAP+Hh4eN6+vrJxwcHP82NjbhTU1NyxoaGvsbGxv1kJCQa////wH///8TcXFxvVlZ
WblaWlq3dHR0j6ampkX///8B////Af///wH///8B////Ad3d3R99fX25enp6pf///wPm5uYLd3d3
r4mJibetra1rWVlZuVlZWblfX1+rd3d3fcXFxRft7e0daWlpvVpaWrdhYWGpcHBwlaurqz3///8B
////Af///wH///8B////Af///wH///8B////Af///wH///8B////Af///wH///8B////Af///wH/
//8B////Af///wH///8B////Af///wH///8B////Af///wH///8B////Af///wH///8B////Af//
/wH///8B////Af///wH///8B////AQAAACkAAABBAAAAQQAAAEEAAABBAAAAQQAAAEEAAABBAAAA
QQAAAEEAAABBAAAAQQAAAEEAAABBAAAAQQAAAEEAAABBAAAAQQAAAEEAAABBAAAAQQAAAEEAAABB
AAAAQQAAAEEAAABBAAAAQQAAAEEAAABBAAAAKf///wH///8BAAAAUQAAAIEAAACBAAAAgQAAAIEA
AACBAAAAgQAAAIEAAACBAAAAgQAAAIEAAACBAAAAgQAAAIEAAACBAAAAgQAAAIEAAACBAAAAgQAA
AIEAAACBAAAAgQAAAIEAAACBAAAAgQAAAIEAAACBAAAAgQAAAIEAAABR////Af///wH///8B////
Af///wH///8B////Af///wH///8B////Af///wH///8B////Af///wH///8B////Af///wH///8B
////Af///wH///8B////Af///wH///8B////Af///wH///8B////Af///wH///8B////Af///wH/
//8B////Af///wH///8B////Af///wH///8B////Af///wH///8B////Af///wH///8B////Af//
/wH///8B////Af///wH///8B////Af///wH///8B////Af///wH///8B////Af///wH///8B////
Af///wH///8B////Af///wH///8B////Af///wH///8B////Af///wH///8B////Af///wH///8B
////Af///wH///8B////Af///wH///8B////Af///wH///8B////Af///wH///8B////Af///wH/
//8B////Af///wH///8B////Af///wH///8B////Af///wH///8B////Af///wH///8B////Af//
/wH///8B////Af///wH///8B////Af///wH///8B////Af///wH///8B////Af///wH///8B////
Af///wH///8B////Af///wH///8B////Af///wH///8B////Af///wH///8B////Af///wH///8B
////Af///wH///8B////Af///wH///8B////Af///wH///8B////Af///wH///8B////Af///wH/
//8B////Af///wH///8B////Af///wH///8B////Af///wH///8B////Af///wH///8B////Af//
/wH///8B////Af///wH///8B////Af///wH///8B////Af///wH///8B////Af///wH///8B////
Af///wH///8B////Af///wH///8B////Af///wH///8B////Af///wH///8B////Af///wH///8B
////Af///wH///8B////Af///wH///8B////Af///wH///8B////Af///wH///8B////Af///wH/
//8B////Af///wH///8B////Af///wH///8B////Af///wH///8B////Af///wH///8B////Af//
/wH///8B////Af///wH///8B////Af///wH///8B////Af///wH///8B////Af///wH///8B////
Af///wH///8B////Af///wH///8B////Af///wH///8B////Af///wH///8B////Af///wH///8B
////Af///wH///8B////Af///wH///8B////Af///wH///8B////Af///wH///8B////Af///wH/
//8B////Af///wH///8B////Af///wH///8B////Af///wH///8B////Af///wH///8B////Af//
/wH///8B////Af///wH///8B////Af///wH///8B////Af///wH///8B////Af///wH///8B////
AQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAA
'''
    fd, icon_fname= tempfile.mkstemp(suffix=".png")
    with os.fdopen(fd) as f:
        pass # just close this one
    with open(icon_fname, "wb") as f:
        f.write(base64.b64decode(icon))
    root.wm_iconbitmap(icon_fname)
    os.remove(icon_fname)

    # Pack bar and label:
    ft = ttk.Frame(height=100, width=300)
    ft.grid(padx=20, pady=40)
    v = StringVar()
    v.set(base_text)
    label = Label(ft, textvariable=v)
    label.pack(expand=True, fill=BOTH, side=TOP)
    pb_hD = ttk.Progressbar(ft, orient='horizontal', mode='indeterminate')
    pb_hD.pack(expand=True, fill=BOTH, side=BOTTOM)
    pb_hD.start(50)

    #Return the label var:    
    return v        

def run_install_with_gui(callback):
    root = Tk()
    root.wm_title("PyXRD Automated installation")
    label = create_progress_bar(root)
    t1 = threading.Thread(target=callback, args=(root, label))
    t1.start()
    root.mainloop()
    t1.join()

def runAsAdmin(commands):
    command = ["runas.exe", "/savecred", "/user:administrator", " ".join(commands)]
    subprocess.call(command)
    
def main():

    if len(sys.argv) == 1:
        print "Executing with elevated privilges"
        args = [sys.executable] + sys.argv + ["restarted"]
        runAsAdmin(args)
    else:
        run_install_with_gui(install_others)
        print "Finished installing!"
    
if __name__ == "__main__":
    main()
                
