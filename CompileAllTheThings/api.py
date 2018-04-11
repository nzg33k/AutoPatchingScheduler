'''
This is my attempt to gather some basic information from multiple places and compile it.

Wish me luck.
'''

import xmlrpclib
from landscape_api.base import API as landscape_api
#This file should be based on configuration.py.template
import configuration as conf

def get_lds_computer_names():
    "Get all the computers in LDS"
    computers = landscape_api(conf.uri, conf.key, conf.secret, conf.ca).get_computers() # pylint: disable=no-member
    computernames = []
    for computer in computers:
        computernames.append(computer["hostname"].encode("utf-8"))
    return computernames

def get_rhs5_computer_names():
    "Get all the computers in RHS5"
    client = xmlrpclib.Server(conf.satellite_url, verbose=0)
    key = client.auth.login(conf.satellite_login, conf.satellite_password)
    computers = client.system.listSystems(key)
    computernames = []
    for computer in computers:
        computernames.append(computer["name"].encode("utf-8"))
    return computernames

def get_computer_names():
    "Get the names of the computers"
    names = get_lds_computer_names()
    names += get_rhs5_computer_names()
    return names

#print len(get_computer_names())
print get_computer_names()
