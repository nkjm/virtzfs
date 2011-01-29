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

class Server_pool:
    def __init__(self):
        self.vmserver_list = vmserver_list
        self.iqn_list = []
    
    def is_vm(self, vm_name):
        for vm in self.vm_list:
            if (vm_name == vm["name"]):
                return True
        return False

    def exist_vmserver(self, vmserver):
        if vmserver in self.vmserver_list:
            return True
        else:
            return False

    def set_iqn_list(self):
        for vmserver in self.vmserver_list:
            cmd = "ssh -l root %s 'cat /etc/iscsi/initiatorname.iscsi | sed \'s/InitiatorName=//g\''" % vmserver
            try:
                res = commands.getoutput(cmd)
                self.iqn_list.append(res)
                return(0)
            except:
                return(1)
            
            

    def get_vm_status(self, vm_name):
        for vm in self.vm_list:
            if (vm_name == vm["name"]):
                return(vm["status"])

    def get_device_path(self, needle):
        cmd = "ssh -l root %(vmserver)s 'ls /dev/disk/by-path | grep -v -- '-part' | grep %(needle)s'" % {"vmserver":self.vmserver_list[0], "needle":needle}
        offset = 0
        while True:
            res = commands.getoutput(cmd)
            device_path = "/dev/disk/by-path/%s" % res
            if device_path == "/dev/disk/by-path/":
                if offset < 5:
                    time.sleep(1)
                    offset = offset + 1
                    continue
                else:
                    print "Device file under /dev/disk/by-path didn't show up."
                    return(None)
            else:
                break
        return(device_path)

    def discover_iscsi_target(self):
        for vmserver in vmserver_list:
            print "  %s... " % vmserver,
            cmd = "ssh -l root %(vmserver)s 'iscsiadm -m discovery -t st -p %(zfs_ip)s > /dev/null 2>&1'" % {"vmserver":vmserver, "zfs_ip":zfs_ip}
            res = os.system(cmd)
            if res == 0:
                print msg_success
            else:
                print msg_fail
                return(1)
        return(0)
    
    def login_to_iscsi_target(self, targetname):
        for vmserver in vmserver_list:
            print "  %s... " % vmserver
            print "    Logging in to %s... " % targetname,
            cmd = "ssh -l root %(vmserver)s 'iscsiadm -m node -T %(targetname)s --login > /dev/null 2>&1'" % {"vmserver":vmserver, "targetname":targetname}
            res = os.system(cmd)
            if res == 0:
                print msg_success
            else:
                print msg_fail
                return(1)
        return(0)
    
    def logout_from_iscsi_target(self, targetname):
        for vmserver in vmserver_list:
            print "  %s... " % vmserver
            print "    Logging out from %s... " % targetname,
            cmd = "ssh -l root %(vmserver)s 'iscsiadm -m node -T %(targetname)s --logout > /dev/null 2>&1'" % {"vmserver":vmserver, "targetname":targetname}
            res = os.system(cmd)
            if res == 0:
                print msg_success
            else:
                print msg_fail
                return(1)
        return(0)

    def delete_iscsi_target(self, targetname):
        for vmserver in vmserver_list:
            print "  %s... " % vmserver
            print "    Deleting iSCSI Target: %s... " % targetname,
            cmd = "ssh -l root %(vmserver)s 'iscsiadm -m node -T %(targetname)s -o delete > /dev/null 2>&1'" % {"vmserver":vmserver, "targetname":targetname}
            res = os.system(cmd)
            if res == 0:
                print msg_success
            else:
                print msg_fail
                return(1)
        return(0)

