#!/usr/bin/python

import os
import stat
import sys
import multiprocessing as mp
import argparse
import logging
import re
from pathlib import Path

# commands:
# - init
# - add
# - rm
# - list
# - store
# - erase
# - get

entpat = re.compile(r"(?P<protocol>[a-z0-9\+]+)://(?P<username>[a-zA-Z0-9\.\-\+]+):(?P<password>[a-zA-Z0-9\.\-\+\*\\@&\^\#\!/$]+)@(?P<host>[a-z0-9\.\:]+)/(?P<path>[a-zA-Z0-9%\./]+\*{0,1})")

def opt():
    home = os.getenv('HOME')
    parser = argparse.ArgumentParser(prog='git-credential-split',
        description='a git credential helper supports multiple separated credential file to add some security',
        formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('-f', '--file', type=str, default=home+'/.config/git-credential-split', action='store', help='file config path')
    parser.add_argument('command', type=str, action='store', nargs='?',
        help='''supported commands:
    init     [-f | --file FILE_PATH] [PATH ...]
    add      PATH ...
    rm       PATH
    list
    store
    erase
    get''')
    parser.add_argument('param', type=str, action='store', nargs='*', help='command parameter')
    return parser.parse_args()

def addLine(f, lf):
    home = os.getenv('HOME')
    for s in lf:
        if s.startswith('/'):
            if stat.S_ISDIR(os.stat(s, follow_symlinks=True).st_mode) == 0:
                pass
            f.write(s+'\n')
        else:
            p = home + os.pathsep + s

def listLoc(args):
    lf = []
    f = open(args.file, 'r')
    while True:
        l = f.readline()
        if l == '':
            break
        lf.append(l[:-1])
    f.close()
    return lf


def add(args):
    if len(args.param) == 0:
        logging.error('no parameter supplied')
        sys.exit(1)

    lf = []
    try:
        lf = listLoc(args)
    except Exception as e:
        logging.error(e)
        sys.exit(1)

    for i in args.param:
        if i in lf:
            logging.error('{0} is in the list'.format(i))
            sys.exit(1)

    f = open(args.file, 'a')
    addLine(f, args.param)
    f.close()

def init(args):
    if os.access(args.file, os.R_OK):
        logging.warning('file {0} is already exist'.format(args.file))
        return
    else:
        try:
            f = open(args.file, 'w')
            addLine(f, args.param)
            f.close()
        except Exception as e:
            logging.error(e)
            sys.exit(1)

def rm(args):
    if len(args.param) == 0:
        logging.error('no parameter supplied')
        return

    lf = []
    try:
        lf = listLoc(args)
    except Exception as e:
        logging.error(e)
        return

    for i in args.param:
        try:
            lf.remove(i)
        except ValueError:
            logging.error('{0} is not in the list'.format(i))
            return

    try:
        f = open(args.file, 'w')
        addLine(f, lf)
        f.close()
    except Exception as e:
        logging.error(e)
    return


def glist(args):
    lf = []
    try:
        lf = listLoc(args)
    except Exception as e:
        logging.error(e)
        return

    for l in lf:
        print(l)

def gitPrep(args):
    cwd = os.getcwd()
    lf = listLoc(args)
    return cwd, lf

def gitStore(cwd, path, data):
    pass

def store(args):
    while True:
        p = sys.stdin.readline(256)
        if p == '\n' or p == '':
            break
    # cwd = None
    # lf = None
    # try:
    #     cwd, lf = gitPrep(args)
    # except Exception as e:
    #     logging.error(e)
    #     sys.exit(1)

    # data = []
    # while True:
    #     l = sys.stdin.readline()
    #     if len(l) == 1 and l[0] == '\n':
    #         break
    #     data.append(l)

    # for f in lf:
    #     pass

def tf():
    home = os.getenv('HOME')
    f = open(home + '/.git-credentials', 'r')
    result = []
    while True:
        l = f.readline(256)
        if l == '':
            break
        if l != '\n':
            l = l.rstrip()
            result.append(l)
    f.close()
    return result

def get(args):
    params = {}
    while True:
        p = sys.stdin.readline(256)
        if p == '\n':
            break
        a = p.split('=', 1)
        if len(a) != 2:
            break
        params[a[0]] = a[1][:-1]

    for l in tf():
        done = False
        while True:
            f = Path(l)
            if f.is_file():
                fg = f.open()
                while True:
                    l = fg.readline(256)
                    if l == '':
                        break
                    l = l.rstrip()

                    m = entpat.match(l)

                    mx = 0
                    for k, v in params.items():
                        if m.group(k) == v:
                            mx += 1
                        elif m.group('path').endswith('*') and v.startswith(m.group('path')[:-1]):
                            mx += 1

                    if mx == 3:
                        # print("protocol={0}".format(m.group('protocol')))
                        # print("host={0}".format(m.group('host')))
                        print("username={0}".format(m.group('username')))
                        print("password={0}".format(m.group('password')))
                        done = True
                        break
                fg.close()
                break
        if done:
            break

def erase(args):
    while True:
        p = sys.stdin.readline(256)
        if p == '\n' or p == '':
            break

def cred(args):
    if args.command == None:
        logging.error('no command supplied')
        return

    if args.command == 'init':
        init(args)
    elif args.command == 'add':
        add(args)
    elif args.command == 'rm':
        rm(args)
    elif args.command == 'list':
        glist(args)
    elif args.command == 'store':
        store(args)
    elif args.command == 'get':
        get(args)
    elif args.command == 'erase':
        erase(args)
    else:
        logging.error('unknown command {0}'.format(args.command))

if __name__ == "__main__":
    logging.basicConfig(format='%(asctime)s %(message)s')
    cred(opt())
