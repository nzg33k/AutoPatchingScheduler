'''
This is my attempt to gather some basic information from multiple places and compile it.

Wish me luck.
'''

#This file should be based on configuration.py.template
import configuration as conf

def get_lds_computer_names():
    "Get all the computers in LDS"
    #https://landscape.canonical.com/static/doc/api/
    from landscape_api.base import API as landscape_api
    computers = landscape_api(conf.URI, conf.KEY, conf.SECRET, conf.CA).get_computers() # pylint: disable=no-member
    computernames = []
    for computer in computers:
        computernames.append(computer["hostname"].encode("utf-8").rstrip().lower())
    return computernames

def get_rhs5_computer_names():
    "Get all the computers in RHS5"
    #https://spacewalkproject.github.io/documentation/api/2.7/
    import xmlrpclib
    client = xmlrpclib.Server(conf.SATELLITE_URL, verbose=0)
    key = client.auth.login(conf.SATELLITE_LOGIN, conf.SATELLITE_PASSWORD)
    computers = client.system.listSystems(key)
    computernames = []
    for computer in computers:
        computernames.append(computer["name"].encode("utf-8").rstrip().lower())
    return computernames

def get_web_computer_names():
    "Get a list of names from a weblist"
    import urllib2
    #Weird proxy stuff here, this will work around it by bypassing the proxy
    if conf.DISABLEPROXY:
        urllib2.getproxies = lambda: {}
    computernames = []
    for weburl in conf.WEBLISTURL:
        computers = urllib2.urlopen(weburl)
        for computer in computers:
            computernames.append(computer.encode("utf-8").rstrip().lower())
    return computernames

def get_googlesheet_computer_names():
    "Get data from google sheets"
    #https://developers.google.com/sheets/api/quickstart/python
    from googleapiclient.discovery import build
    from httplib2 import Http
    from oauth2client import file as gfile, client, tools
    #Setup the Sheets API
    scopes = 'https://www.googleapis.com/auth/spreadsheets.readonly'
    store = gfile.Storage('credentials.json')
    creds = store.get()
    if not creds or creds.invalid:
        flow = client.flow_from_clientsecrets('client_secret.json', scopes)
        creds = tools.run_flow(flow, store)
    service = build('sheets', 'v4', http=creds.authorize(Http()))
    # Call the Sheets API
    computernames = []
    for gsheet in conf.GSHEETS:
        result = service.spreadsheets().values() # pylint: disable=no-member
        result = result.get(spreadsheetId=gsheet['id'], range=gsheet['range'])
        result = result.execute()
        values = result.get('values', [])
        if values:
            for row in values:
                computernames.append(row[0].encode("utf-8").rstrip().lower())
    return computernames

def get_computer_names():
    "Get the names of the computers"
    names = get_lds_computer_names()
    names += get_rhs5_computer_names()
    names += get_web_computer_names()
    names += get_googlesheet_computer_names()
    return list(set(names))

print get_computer_names()
