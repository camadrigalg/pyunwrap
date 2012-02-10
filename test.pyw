PK      3H@w%7|�  �     __main__#!/usr/bin/env python
#-*- coding: UTF-8 -*-

"""
Este es un script que busca actualizar el repositorio en que se halla
aprovechando git. Debe funcionar en GNU/Linux y en Windows, especialmente en
este último donde es más probable que el entorno esté incompleto o
desactualizado.
"""

from Queue import Queue, Empty
from src import autopipe
from src.executables import get_paths
from subprocess import Popen, PIPE, STARTUPINFO, SW_HIDE, STARTF_USESHOWWINDOW
from threading  import Thread
import sys
import webbrowser


def enqueue_output(out, queue):
    for line in iter(out.read, ''):
        queue.put(line)
    out.close()


def non_blocking_proc(command):
    sys.stderr.write("» Launch: %s\n" % (" ".join(command)).lower(), "blue")
    info = STARTUPINFO()
    info.dwFlags |= STARTF_USESHOWWINDOW
    info.wShowWindow = SW_HIDE

    proc = Popen(command, stdout=PIPE, stderr=PIPE, bufsize=1,
        close_fds=False, startupinfo=info)

    stdout_queue = Queue()
    stdout = Thread(target=enqueue_output, args=(proc.stdout,
        stdout_queue))
    stdout.daemon = True
    stdout.start()

    stderr_queue = Queue()
    stderr = Thread(target=enqueue_output, args=(proc.stderr,
        stderr_queue))
    stderr.daemon = True
    stderr.start()

    while proc.poll() is None:

        try:
            line = stdout_queue.get_nowait()
        except Empty:
            pass
        else:
            sys.stdout.write("    " + line)

        try:
            line = stderr_queue.get_nowait()
        except Empty:
            pass
        else:
            sys.stderr.write("    " + line)

    return proc.returncode


def check_module(name, module):
    sys.stdout.write("    Cheking %s: " % name, "blue")
    try:
        module = __import__(module)
        print "pass"
        return module
    except ImportError:
        sys.stderr.write("fail\n")
        return False


def execute(path):
    sys.stderr.write("""***     Executing installer\n"""
        """***     execute & retry\n""")
    return non_blocking_proc([path])


def download(url):
    sys.stderr.write("""***     Fetching installer\n"""
        """***     execute & retry\n""")
    return webbrowser.open(url)


def easy_install(module):
    easy_install_paths = get_paths("easy_install")
    command = [easy_install_paths[0], module]
    non_blocking_proc(command)


def pip_install(module):
    pip_paths = get_paths(r"pip")
    command = [pip_paths[0], "install", module]
    non_blocking_proc(command)


def main():
    "The main routine"

    sys.stderr.write("Verifing git: ", "blue")
    git_paths = get_paths(r"git\cmd\git")
    if not git_paths:
        sys.stderr.write("fail\n")
        download("https://code.google.com/p/msysgit/downloads/detail?"
            "name=Git-1.7.9-preview20120201.exe")
        return 1
    else:
        print("pass")

    commands = [
        [git_paths[0], "stash"],
        [git_paths[0], "fetch", "-v"],
        [git_paths[0], "rebase", "-v"]
    ]

    for command in commands:
        non_blocking_proc(command)

    methods = {
        "executable" : execute,
        "easy_install" : easy_install,
        "download" : download,
        "pip" : pip_install
    }

    sys.stderr.write("\nTesting dependencies:\n")
    lines = (line.strip().split(";") for line in open("dependencies.txt"))
    for name, module, method, argument in lines:
        if not check_module(name, module):
            methods[method](argument)


if __name__ == "__main__":
    exit(main())
PK     �yI@T0;�   �      src/autopipe.py#!/usr/bin/env python
#-*- coding: UTF-8 -*-

import os
import sys

if os.name in ("nt", "posix"):
    import tkpipe
    pipe = tkpipe.Tkpipe()
    sys.stdout = pipe.default("green")
    sys.stderr = pipe.default("red")
PK     m�I@B23Lr  r     src/tkpipe.py#!/usr/bin/env python
#-*- coding: UTF-8 -*-

from Tkinter import Button, Frame, Label, Text
import ImageTk

class Tkpipe(Frame):

    def __init__(self, title="Standard output", label="Propram progress"):
        Frame.__init__(self)
        self.master.title(title)
        self.grid(stick="nsew")
        self.createWidgets()
        self.label = label
        self.closed = False
        self.images = []


    def createWidgets(self):
        top = self.winfo_toplevel()

        top.rowconfigure(0, weight=1, minsize=96)
        top.columnconfigure(0, weight=1)

        self.columnconfigure(0, weight=1)

        self.rowconfigure(0, minsize=24)
        self.lbl_pretext = Label(self, text="Update progress:")
        self.lbl_pretext.grid(row=0, sticky="w")

        self.rowconfigure(1, minsize=48, weight=1)
        self.txt_messages = Text(self)
        self.txt_messages.grid(row=1, sticky="nsew")
        self.txt_messages.config(selectbackground="#d2d3bd")
        self.txt_messages.tag_config("green", foreground="darkgreen")
        self.txt_messages.tag_config("blue", foreground="darkblue")
        self.txt_messages.tag_config("red", foreground="darkred")

        self.rowconfigure(2, minsize=24)
        self.btn_quit = Button(self, text="Quit", command=self.quit)
        self.btn_quit.grid(row=2, sticky="ew")

        self.write("Process started\n-----\n", "blue")
        self.update()


    def write(self, line, tag=None):
        line = line.replace("\r\n", "\n")
        self.txt_messages.insert("end", line, tag)
        self.txt_messages.see("end")
        self.txt_messages.update()


    def writelines(self, iterable, tag=None):
        for line in iterable:
            self.write(line, tag)


    def flush(self):
        self.update()


    def close(self):
        if not self.closed:
            self.write("-----\nProcess ended", "blue")
            self.closed = True
            self.mainloop()


    def default(self, tagname):
        return ColoredPipe(self, tagname)


    def __del__(self, *args):
        self.close()

    def writeimage(self, image):
        self.images.append(ImageTk.PhotoImage(image))
        self.txt_messages.image_create("end", {"image" : self.images[-1]})
        self.write("\n")
        self.update()


class ColoredPipe:

    def __init__(self, pipe, tag):
        self.pipe = pipe
        self.default_tag = tag


    def default(self, tagname):
        return ColoredPipe(self.pipe, tagname)


    def write(self, string, tag=None):
        self.pipe.write(string, tag or self.default_tag)


    def writelines(self, iterable, tag=None):
        for line in iterable:
            self.write(line, tag or self.default_tag)

    def flush(self):
        self.pipe.flush()

    def close(self):
        self.pipe.close()

    def __del__(self, *args):
        self.pipe.__del__(*args)

    def writeimage(self, image):
        self.pipe.writeimage(image)
PK      3H@w%7|�  �             ��    __main__PK     �yI@T0;�   �              ���  src/autopipe.pyPK     m�I@B23Lr  r             ���  src/tkpipe.pyPK      �   y    