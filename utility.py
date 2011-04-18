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

class Utility:
    def ask_yes_or_no(self):
        for line in iter(sys.stdin.readline, ""):
            if (line == "y\n"):
                print ""
                break
            elif (line == "n\n"):
                sys.exit()
            else:
                print "Enter just 'y' or 'n'. [y/n]: ",

    def get_yes_or_no(self):
        for line in iter(sys.stdin.readline, ""):
            if (line == "y\n"):
                return("yes")
            elif (line == "n\n"):
                return("no")
            else:
                print "Enter just 'y' or 'n'. [y/n]: ",
    
    def is_valid_name(self, input):
        vm_name_rule = string.lowercase + string.uppercase + string.digits + "._"
        for i in input:
            if not i in vm_name_rule:
                return False
        return True

    def get_new_mac_address(self):
        mac = [ 0x00, 0x16, 0x3e, random.randint(0x00, 0x7f), random.randint(0x00, 0xff), random.randint(0x00, 0xff) ]
        return ':'.join(map(lambda x: "%02x" % x, mac))

    def interview(self, question, choice_list, default):
        if (choice_list is None):
            if not default is None:
                print "Please enter %s (just Enter to accept default '%s'): " % (question, default),
            else:
                print "Please enter %s: " % question,

            for line in iter(sys.stdin.readline, ""):
                answer = line.replace("\n","")
                if not (default is None) and (answer == ""):
                    print ""
                    return (default)
                elif (default is None) and (answer == ""):
                    print ""
                    print "Please enter %s: " % question,
                    continue
                break
            print ""
            return (answer)
        else:
            print "Please select %s from following list. (Enter the number)" % question
            if not default is None:
                print "(just Enter to accept default '%s')" % default
            offset = 0
            for choice in choice_list:
                print "\t[%s] %s" % (offset, choice)
                offset = offset + 1
            print "Answer: ",
            for line in iter(sys.stdin.readline, ""):
                answer = line.replace("\n","")
                if not (default is None) and (answer == ""):
                    print ""
                    return (default)
                else:
                    try:
                        answer = int(answer)
                    except:
                        print "Invalide answer. Please enter the NUMBER [0-%s]." % (offset - 1) 
                        print "Answer: ",
                        continue

                if (int(answer) >= 0) and (int(answer) < offset):
                    print ""
                    return (choice_list[int(answer)])
                else:
                    print "Invalide answer. Please enter the NUMBER [0-%s]." % (offset - 1) 
                    print "Answer: ",

    def get_number(self, question, input, default):
        if input is None:
            try:
                number = self.interview(question=question, choice_list=None, default=default)
            except:
                sys.exit()
        else:
            number = input

        while True:
            if not (number.isdigit()) or number == "0":
                print "Specified %s is not valid" % question
            else:
                break
            try:
                number = self.interview(question=question, choice_list=None, default=default)
            except:
                sys.exit()
        return(number)

    def get_new_name(self, question, choice_list, input, default):
        if input is None:
            try:
                name = self.interview(question=question, choice_list=None, default=default)
            except:
                sys.exit()
        else:
            name = input

        while True:
            if name in choice_list:
                print "Specified NEW %s already exist in ZFS repository. Please try another name." % question
            elif not self.is_valid_name(name):
                print "Specified NEW %s not valid. Valid letters are [a-zA-Z0-9._]" % question
            else:
                break
            try:
                name = self.interview(question=question, choice_list=None, default=default)
            except:
                sys.exit()
        return(name)

    def get_name(self, question, choice_list, input, default):
        if input is None:
            try:
                name = self.interview(question=question, choice_list=choice_list, default=default)
            except:
                sys.exit()
        else:
            name = input
            while not name in choice_list:
                print "Specified %s does not in ZFS repository." % question
                try:
                    name = self.interview(question=question, choice_list=choice_list, default=default)
                except:
                    sys.exit()
        return(name)

    def get_name_list(self, question, choice_list, input, default):
        dynamic_list = list(choice_list)
        name_list = []
        while True:
            if not len(name_list) == 0:
                dynamic_list.append("That's it.")
            name = self.get_name(question=question, choice_list=dynamic_list, input=input, default=default)
            dynamic_list.remove(name)
            if name == "That's it.":
                break
            if not name in name_list:
                name_list.append(name)
            print "Selected %s:" % question
            for i in name_list:
                print "\t" + i
            print ""
            try:
                dynamic_list.remove("That's it.")
            except:
                pass
            if len(dynamic_list) < 1:
                break
        return(name_list)


