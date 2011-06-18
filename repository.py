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

class Repository:
    def __init__(self):
        self.path_root = repository_root
        self.path_domain = "%(path_root)s/%(dir_domain)s" % {"path_root":self.path_root,"dir_domain":dir_domain}
        self.path_vm = "%(path_root)s/%(dir_vm)s" % {"path_root":self.path_root,"dir_vm":dir_vm}
        self.path_template = "%(path_root)s/%(dir_template)s" % {"path_root":self.path_root,"dir_template":dir_template}
        self.path_shareddisk = "%(path_root)s/%(dir_shareddisk)s" % {"path_root":self.path_root,"dir_shareddisk":dir_shareddisk}
        self.tpg = zfs_ip
        self.hg = comstar_hostgroup_name
        self.vm_list = []
        self.template_list = []
        self.shareddisk_list = []
        self.snapshot_list = []

    def set_template_list(self):
        cmd = "pfexec /usr/sbin/zfs list -H -r -t filesystem %s | sed -e '1d' | cut -f1 | sed 's?^.*/??g'" % self.path_template
        res = commands.getoutput(cmd)
        self.template_list = res.splitlines()

    def set_vm_list(self):
        cmd = "pfexec /usr/sbin/zfs list -H -r -t filesystem %s | sed -e '1d' | cut -f1 | sed 's?^.*/??g'" % self.path_vm
        res = commands.getoutput(cmd)
        self.vm_list = res.splitlines()

    def set_shareddisk_list(self):
        cmd = "pfexec /usr/sbin/zfs list -H -r -t volume %s | cut -f1 | sed 's?^.*/??g'" % self.path_shareddisk
        res = commands.getoutput(cmd)
        self.shareddisk_list = res.splitlines()

    def get_latest_snapshot(self, volume):
        cmd = "pfexec /usr/sbin/zfs list -H -r -o name -S creation -t snapshot %s | head -1 | sed \'s/^.*@//g\'" % volume
        latest_snapshot = commands.getoutput(cmd)
        return(latest_snapshot)

    def get_guid(self, lu_source):
        cmd = "pfexec /usr/sbin/sbdadm list-lu | grep %s$ | cut -d' ' -f1" % lu_source
        res = commands.getoutput(cmd)
        return(res)

    def get_lun(self, lu_guid):
        cmd = "pfexec /usr/sbin/stmfadm list-view -l %s | grep 'LUN          :' | awk '{ print $3 }'" % lu_guid
        res = commands.getoutput(cmd)
        return(res)

    def get_filesize(self, file_path):
        cmd = "ls -l %s | awk '{print $5}'" % file_path
        res = commands.getoutput(cmd)
        return(res)

    def exist(self):
        cmd = "pfexec /usr/sbin/zfs list -H %s > /dev/null 2>&1" % self.path_root
        if os.system(cmd) == 0:
            return True
        else:
            return False

    def exist_template(self, template_name):
        self.set_template_list()
        if template_name in self.template_list:
            return True
        else:
            return False

    def exist_vm(self, vm_name):
        self.set_vm_list()
        if vm_name in self.vm_list:
            return True
        else:
            return False

    def create_snapshot(self, path, snapshot_name):
        cmd = "pfexec /usr/sbin/zfs list %s > /dev/null 2>&1" % path
        res = os.system(cmd)
        if not res == 0:
            print "Specified path: %s does not exist" % path
            return(1)

        # check if specified snapshot name does not exist
        while True:
            cmd = "pfexec /usr/sbin/zfs list -t snapshot %(path)s@%(snapshot_name)s > /dev/null 2>&1" % {"path":path,"snapshot_name":snapshot_name}
            res = os.system(cmd)
            if res == 0:
                default_snapshot_name = time.strftime("%Y_%m_%d_%H_%M_%S")
                print "Specified Snapshot Name already exists."
                try:
                    snapshot_name = utility.interview(question="SNAPSHOT NAME", choice_list=None, default=default_snapshot_name)
                except:
                    return(1)
            else:
                break

        cmd = "pfexec /usr/sbin/zfs snapshot -r %(path)s@%(snapshot_name)s" % {"path":path,"snapshot_name":snapshot_name}
        res = os.system(cmd)
        return(res)

    def delete_snapshot(self, path, snapshot_name):
        cmd = "pfexec /usr/sbin/zfs list -t snapshot %(path)s@%(snapshot_name)s > /dev/null 2>&1" % {"path":path,"snapshot_name":snapshot_name}
        res = os.system(cmd)
        if not res == 0:
            print "Specified Snapshot Name does not exist."
            return(1)
        cmd = "pfexec /usr/sbin/zfs destroy -r %(path)s@%(snapshot_name)s" % {"path":path,"snapshot_name":snapshot_name}
        res = os.system(cmd)
        return(res)

    def rollback(self, path, snapshot_name=None):
        cmd = "pfexec /usr/sbin/zfs rollback -r %s@%s" % (path, snapshot_name)
        res = os.system(cmd)
        return(res)

    def initialize(self, iqn_list):
        ### Create repository and Enable iSCSI target on those filesystem
        # confirm specified Repository does not exist
        if self.exist():
            # repository detected so skip.
            print "Repository: '%s' already exists on ZFS so skip create it." % self.path_root
        else:
            # create repository
            print "\nCreating repository: '%s'... " % self.path_root,
            cmd = "\
                pfexec /sbin/zfs create -p %(path_root)s && \
                pfexec /sbin/zfs create -p -o sharenfs=rw,anon=0 %(path_domain)s && \
                pfexec /sbin/zfs create -p -o dedup=%(dedup)s %(path_template)s && \
                pfexec /sbin/zfs create -p %(path_vm)s && \
                pfexec /sbin/zfs create -p %(path_shareddisk)s" % {
                "dedup":dedup,
                "path_root":self.path_root,
                "path_domain":self.path_domain,
                "path_template":self.path_template,
                "path_vm":self.path_vm,
                "path_shareddisk":self.path_shareddisk
            }
            if os.system(cmd) == 0:
                print msg_success
            else:
                print msg_fail
                return 1

        ### Create Target Port Group in case ZFS node has multiple NIC.
        # confirm specified Target Port Group does not exist
        cmd = "pfexec /usr/sbin/itadm list-tpg %s > /dev/null 2>&1" % self.tpg
        if os.system(cmd) == 0:
            # Target Port Group detected. Skip.
            print "Target Port Group: '%s' already exists so skip to create it." % self.tpg
        else:
            # create Target Port Group 
            print "Creating Target Port Group: '%s'... " % self.tpg,
            cmd = "pfexec /usr/sbin/itadm create-tpg %s %s > /dev/null 2>&1" % (self.tpg, zfs_ip)
            if os.system(cmd) == 0:
                print msg_success
            else:
                print msg_fail
                return 1

        ### Create Host Group
        # confirm specified Host Group does not exist
        cmd = "pfexec /usr/sbin/stmfadm list-hg %s > /dev/null 2>&1" % self.hg
        if os.system(cmd) == 0:
            # Host Group detected so skip.
            print "Host Group: '%s' detected so skip to create it." % self.hg
        else:
            # create Host Group
            print "Creating Host Group: '%s'... " % self.hg,
            cmd = "pfexec /usr/sbin/stmfadm create-hg %s > /dev/null 2>&1" % self.hg
            if os.system(cmd) == 0:
                print msg_success
            else:
                print msg_fail
                return 1

        ### Add Host Group Member to Host Group
        for iqn in iqn_list:
            # confirm specified client IQN does not belong to Host Group yet.
            cmd = "pfexec /usr/sbin/stmfadm list-hg -v | grep %s$ > /dev/null 2>&1" % iqn
            if os.system(cmd) == 0:
                # IQN detected so skip.
                print "Client IQN: '%s' already belongs to Host Group: '%s' so skip to process." % (iqn, self.hg)
            else:
                print "Adding Member:'%s' to Host Group:'%s'... " % (iqn, self.hg),
                cmd = "pfexec /usr/sbin/stmfadm add-hg-member -g %s %s > /dev/null 2>&1" % (self.hg, iqn)
                if os.system(cmd) == 0:
                    print msg_success
                else:
                    print msg_fail
                    return 1

        print "\nRepository successfully initialized.\n"
