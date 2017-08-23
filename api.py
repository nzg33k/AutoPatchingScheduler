'''
This will schedule autopatching for all systems in groups with names starting with <PREFIX>.
The systems will be tagged and all available errata will be applied.
The settings are set in RHS, not here.

The schedule will be created for next month and the schedule information will be grabbed from the end of the group description.
This will be formatted:

###<DayOfWeek> <Week Of Month> <Time> <RebootPlan>

The values are:
###<0-7> <1-4> <00:00 - 23:59> <Always|IfNeeded|Never>
    - DOW 0 is Sunday
    - Week Of Month - 1 is the first week.    Values over 4 haven't been tested and will probably work inconsistently, don't do it.
    - Time is in 24 hour time
    - RebootPlan
        - Always - reboot everytime we path.
        - Never - do not reboot.
        - IfNeeded - reboot if a reboot is needed, otherwise don't.    **NOTE** This doesn't work yet as knowing when it is needed is hard.

The only configurable values are PREFIX and STARTDATE
'''
import xmlrpclib
import datetime
import random
import string
import re
#This file should be based on SatelliteCredentials.py.template
import SatelliteCredentials

PREFIX = "APmytestgroup" #All groups that start with this will be processed
STARTDATE = None #If you want to schedule for any month other than next, change this

client = xmlrpclib.Server(SatelliteCredentials.SATELLITE_URL, verbose=0)

key = client.auth.login(SatelliteCredentials.SATELLITE_LOGIN, SatelliteCredentials.SATELLITE_PASSWORD)

def id_generator(size=12, chars=string.ascii_uppercase + string.digits):
    "Create a nice random string - we will use this for tagnames and action chain names"
    return ''.join(random.choice(chars) for _ in range(size))

def tag_group_system(key, systemid, tagname=id_generator()):
    "This will tag the latest snapshot for a system with the name <tagname>"
    snaplist = client.system.provisioning.snapshot.list_snapshots(key, systemid, {})
    client.system.provisioning.snapshot.addTagToSnapshot(key, snaplist[0].get('id'), tagname)

def schedule_outstanding_errata(key, system, date, reboot="Always", chainname=id_generator()):
    "This will schedule an action chain of all outstanding errata for the system"
    errataset = client.system.getRelevantErrata(key, system)
    earray = []
    #getRelevantErrata gives us an array of errata (which are arrays of errata details), but addErrataUpdate needs an array of errata ids
    for errata in errataset:
        earray.extend([int(errata.get('id'))])
    client.actionchain.createChain(key, chainname)
    client.actionchain.addErrataUpdate(key, system, earray, chainname)
    if reboot == "Always":
        client.actionchain.addSystemReboot(key, system, chainname)
    elif reboot == "IfNeeded":
        #Maybe one day we'll have more smarts in here, till then a reboot is always required
        client.actionchain.addSystemReboot(key, system, chainname)
    client.actionchain.scheduleChain(key, chainname, date)

def get_groups(key=key, prefix=PREFIX, startdate=STARTDATE):
    "Get a list of groups with the right prefix"
    groups = client.systemgroup.listAllGroups(key)
    groups = [group for group in groups if group.get('name').startswith(prefix)]
    for group in groups:
        group = set_group_arguments(group, startdate) #Set the date etc
    return groups

def find_date(startdate, weekday, weeknumber):
    "Find the date that is the <weekday> of the <weeknumber> week after <date>.    1=Monday, The first weekday after date is considered weeknumber 1"
    daysahead = weekday - (startdate.weekday()+1) #The +1 makes this match up with linux times (day 1 = Monday)
    if daysahead <= 0:
        #Target day already happened this week
        daysahead += 7
    #Add 7 days for each Week Of Month we want - but 'This' week is week 1
    daysahead += 7*(weeknumber-1)
    return startdate + datetime.timedelta(daysahead)

def next_month(workingdate=None):
    "Find the start of the month after <workingdate>"
    if not workingdate:
        workingdate = datetime.datetime.now()
    workingdate = workingdate.replace(day=1)
    #If it's December then next month is January next year not month 13 of this year
    if workingdate.month == 12:
        workingdate = workingdate.replace(month=1)
        workingdate = workingdate.replace(year=(workingdate.year+1))
    else:
        workingdate = workingdate.replace(month=(workingdate.month+1))
    return workingdate

def set_group_arguments(group, startdate=STARTDATE):
    "Set the date to schedule the work for"
    #We just want the arguments from the end of the description
    group['arguments'] = re.sub(r"^(.|\n)*###", "", group.get('description'))
    arguments = re.split(" ", group['arguments'])
    arguments[2] = re.split(":", arguments[2])
    group['schedule'] = find_date(next_month(startdate).replace(hour=int(arguments[2][0])).replace(minute=int(arguments[2][1])), int(arguments[0]), int(arguments[1]))
    group['reboot'] = arguments[3]
    return group

def patch_groups(key=key, prefix=PREFIX, startdate=STARTDATE):
    "Actually schedule the work for matching systems.    You can set startdate to the month before the month you want to schedule for, but normally you just want to schedule for next month so it should be set to None."
    groups = get_groups(key, prefix, startdate)
    for group in groups:
        systems = client.systemgroup.listSystemsMinimal(key, group['name'])
        for system in systems:
            tag_group_system(key, system['id'])
            schedule_outstanding_errata(key, system['id'], group['schedule'], group['reboot'])

patch_groups(key, PREFIX, STARTDATE)

client.auth.logout(key)
