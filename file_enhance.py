#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
# Copyright (C) 2014 Kurten Chan <chinkurten@gmail.com>
#
# Distributed under terms of the MIT license.

"""
file copy cut paste application command plugin
"""
import os
import sublime
import sublime_plugin
from shutil import *



class FilesCopyCommand(sublime_plugin.WindowCommand):
    def run(self, **args):
        FilesPasteCommand.g_dirs = args.get('dirs')
        FilesPasteCommand.g_files = args.get('files')
        FilesPasteCommand.g_opcode = 1


class FilesCutCommand(sublime_plugin.WindowCommand):
    def run(self, **args):
        FilesPasteCommand.g_dirs = args.get('dirs')
        FilesPasteCommand.g_files = args.get('files')
        FilesPasteCommand.g_opcode = 2

class FilesPasteCommand(sublime_plugin.WindowCommand):
    g_dirs = None
    g_files = None
    g_opcode = 1  # 1 copy, 2 cut
    
    def run(self, **args):
        dirs = args.get('dirs')
        files = args.get('files')
        dst = None
        if len(dirs) > 0:
            dst = dirs[0]
        elif len(files) > 0:
            f = files[0]
            dst = os.path.dirname(f)

        if dst == None:
            return

        if FilesPasteCommand.g_opcode == 1:
            copy_to(dst)

        elif FilesPasteCommand.g_opcode == 2:
            move_to(dst)

        FilesPasteCommand.g_dirs = None 
        FilesPasteCommand.g_files = None

    def is_enabled(self):
        if FilesPasteCommand.g_dirs != None or FilesPasteCommand.g_files != None:
            return True
        return False


def copy_to(dst):
    if FilesPasteCommand.g_dirs != None:
        for dir in FilesPasteCommand.g_dirs:
            d, op = checkAndShow(dir, dst)
            if op == 0:
                copy_recursive(dir, d)
            elif op == 1:
                copy_recursive(dir, d, True)

    if FilesPasteCommand.g_files != None:
        for file in FilesPasteCommand.g_files:
            d, op = checkAndShow(file, dst)
            if op == 0:
                copy2(file, d)   
            elif op == 1:
                os.remove(d)
                copy2(file, d)

def move_to(dst):
    if FilesPasteCommand.g_dirs != None:
        for dir in FilesPasteCommand.g_dirs:
            d, op = checkAndShow(dir, dst)
            if op == 0:
                move(dir, dst)
            elif op == 1:
                copy_recursive(dir, d, True)
                rmtree(dir)

    if FilesPasteCommand.g_files != None:
        for file in FilesPasteCommand.g_files:
            d, op = checkAndShow(file, dst)
            if op == 0:
                move(file, dst)
            elif op == 1:
                os.remove(d)
                move(file, d)

def checkAndShow(src, dst):
    name = os.path.basename(src)
    t = os.path.join(dst, name)
    if os.path.exists(t):
        msg = 'Path: ' + t + ' is exists, Overwriting?'
        if sublime.ok_cancel_dialog(msg): # cancel than return
            return t, 1
        else:
            return t, 2
    return t, 0


def copy_recursive(src, dst, over=False):
    if src == dst and over == False:
        sublime.error_message('Can copy to the same folder!')
        return
    names = os.listdir(src)
    if os.path.exists(dst):
        if over == False:
            msg = 'Path: ' + dst + ' is exists, Overwriting?'
            if sublime.ok_cancel_dialog(msg) == False: # cancel than return
                return
    else:
        os.makedirs(dst)
    errors = []
    for name in names:
        srcname = os.path.join(src, name)
        dstname = os.path.join(dst, name)
        try:
            if os.path.islink(srcname):
                linkto = os.readlink(srcname)
                os.symlink(linkto, dstname)
            elif os.path.isdir(srcname):
                copy_recursive(srcname, dstname, over)
            else:
                if over and os.path.exists(dstname):
                    os.remove(dstname)
                copy2(srcname, dstname)
            # XXX What about devices, sockets etc.?
        except (IOError, os.error) as why:
            errors.append((srcname, dstname, str(why)))
        # catch the Error from the recursive copytree so that we can
        # continue with other files
        except Error as err:
            errors.extend(err.args[0])
    try:
        copystat(src, dst)
    except WindowsError:
        # can't copy file access times on Windows
        pass
    except OSError as why:
        errors.extend((src, dst, str(why)))

    if errors:
        print(errors)