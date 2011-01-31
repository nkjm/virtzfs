#!/usr/bin/python

### User Configurable Parameters
zfs_ip = ""
vmserver_list = [""]
repository_name = ""

### Do not edit below
repository_root = "rpool/%s" % repository_name
iqn_base = "iqn.0000-00.%s" % repository_name
comstar_hostgroup_name = "virtzfs"
shareddisk_prefix = "sdisk"
dir_domain = "nfs"
dir_vm = "running_pool"
dir_template = "seed_pool"
dir_shareddisk = "sharedDisk"
msg_success = "[SUCCEEDED]"
msg_fail = "[FAILED]"
