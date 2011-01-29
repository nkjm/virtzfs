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
        self.backend = None
        self.frontend = None
        self.permission = "w!"

    def get_targetname(self):
        name = re.sub('_', '', self.name)
        name = name.lower()
        targetname = "%(iqn_base)s:%(shareddisk_prefix)s%(name)s" % {"iqn_base":iqn_base,"shareddisk_prefix":shareddisk_prefix,"name":name}
        return(targetname)

    def get_backend(self, zfs_ip, targetname, lun):
        backend = "/dev/disk/by-path/ip-%(zfs_ip)s:3260-iscsi-%(targetname)s-lun-%(lun)s" % {"zfs_ip":zfs_ip, "targetname":targetname, "lun":lun}
        return(backend)
