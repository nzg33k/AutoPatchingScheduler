'''
This is my attempt to gather some basic information from multiple places and compile it.

Wish me luck.
'''

import xmlrpclib
import urllib2
from landscape_api.base import API as landscape_api
#This file should be based on configuration.py.template
import configuration as conf

def get_lds_computer_names():
    "Get all the computers in LDS"
    computers = landscape_api(conf.URI, conf.KEY, conf.SECRET, conf.CA).get_computers() # pylint: disable=no-member
    computernames = []
    for computer in computers:
        computernames.append(computer["hostname"].encode("utf-8"))
    return computernames

def get_rhs5_computer_names():
    "Get all the computers in RHS5"
    client = xmlrpclib.Server(conf.SATELLITE_URL, verbose=0)
    key = client.auth.login(conf.SATELLITE_LOGIN, conf.SATELLITE_PASSWORD)
    computers = client.system.listSystems(key)
    computernames = []
    for computer in computers:
        computernames.append(computer["name"].encode("utf-8"))
    return computernames

def get_web_computer_names():
    "Get a list of names from a weblist"
    #Weird proxy stuff here, this will work around it by bypassing the proxy
    if conf.DISABLEPROXY:
        urllib2.getproxies = lambda: {}
    computernames = []
    for weburl in conf.WEBLISTURL:
        computers = urllib2.urlopen(weburl)
        for computer in computers:
            computernames.append(computer.encode("utf-8").rstrip())
    return computernames

def get_computer_names():
    "Get the names of the computers"
    names = get_lds_computer_names()
    names += get_rhs5_computer_names()
    names += get_web_computer_names()
    return list(set(names))

print get_computer_names()
print len(get_computer_names())
