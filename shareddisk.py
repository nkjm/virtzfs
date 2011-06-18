#!/usr/bin/python

import commands
import copy
import optparse
import os
import shutil
import socket
import string
import sys
import tempfile
import random
import re
import time

from config import *
from utility import Utility
utility = Utility()

class Shareddisk:
    def __init__(self, name, size=None):
        self.name = name
        self.name_w_prefix = shareddisk_prefix + name
        self.size = size
        self.targetname = self.get_targetname()
        self.targetgroupname = self.get_targetgroupname()
        self.backend = None
        self.frontend = None
        self.permission = "w!"
        self.snapshot_list = []

    def get_targetname(self):
        name = re.sub('_', '', self.name)
        name = name.lower()
        targetname = "%(iqn_base)s:%(shareddisk_prefix)s%(name)s" % {"iqn_base":iqn_base,"shareddisk_prefix":shareddisk_prefix,"name":name}
        return(targetname)

    def get_targetgroupname(self):
        targetgroupname = "%s:%s%s" % (repository_name, shareddisk_prefix, self.name)
        return(targetgroupname)

    def get_backend(self, zfs_ip, targetname, lun):
        backend = "/dev/disk/by-path/ip-%(zfs_ip)s:3260-iscsi-%(targetname)s-lun-%(lun)s" % {"zfs_ip":zfs_ip, "targetname":targetname, "lun":lun}
        return(backend)

    def set_snapshot_list(self):
        cmd = "pfexec /usr/sbin/zfs list -H -r -o name -S creation -t snapshot %s/%s/%s | sed 's/^.*@//g' | uniq" % (repository_root, dir_shareddisk, self.name)
        res = commands.getoutput(cmd)
        self.snapshot_list = res.splitlines()
