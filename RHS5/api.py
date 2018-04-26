'''
This will schedule autopatching for all systems in groups with names starting with <PREFIX>.
The systems will be tagged and all available errata will be applied.
The settings are set in RHS, not here.

The schedule will be created for next month and the schedule information will be grabbed from RHS.
Specically the information will be taken from the end of the group description.
This will be formatted:

###Args:<DayOfWeek> <Week Of Month> <Time> <RebootPlan>

The values are:
###Args:<0-7> <1-4> <00:00 - 47:59> <Always|IfNeeded|Never>
    - DOW 0 is Sunday.
    - Week Of Month - 1 is the first week.    Values over 4 haven't been tested.
    - Time is in 24 hour time.  Hours over 23 will refer to hour-24 the next day.
    - RebootPlan:
        - Always - reboot everytime we path.
        - Never - do not reboot.
        - IfNeeded - reboot if a reboot is needed, otherwise don't.
          **NOTE** This doesn't work yet as knowing when it is needed is hard.

The only configurable values are in configuration.py.
You should base configuration.py on configuration.py.template
'''
import xmlrpclib
import datetime
import random
import string
import re

def id_generator(size=12, chars=string.ascii_uppercase + string.digits):
    "Create a nice random string - we will use this for tagnames and action chain names"
    return ''.join(random.choice(chars) for _ in range(size))

def tag_group_system(client, key, systemid, tagname=""):
    "This will tag the latest snapshot for a system with the name <tagname>"
    tagname += datetime.datetime.now().strftime("%Y%m%d%H%M%S%f")
    snaplist = client.system.provisioning.snapshot.list_snapshots(key, systemid, {})
    client.system.provisioning.snapshot.addTagToSnapshot(key, snaplist[0].get('id'), tagname)

def schedule_pending_errata(client, key, system, date, reboot):
    "This will schedule an action chain of all outstanding errata for the system"
    chainname = datetime.datetime.now().strftime("%Y%m%d%H%M%S%f") + str(system)
    errataset = client.system.getRelevantErrata(key, system)
    if errataset:
        earray = []
        #getRelevantErrata gives us an array of errata (which are arrays of errata details).
        #addErrataUpdate needs an array of errata ids
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

def get_groups(client, key, prefix, startdate):
    "Get a list of groups with the right prefix"
    groups = client.systemgroup.listAllGroups(key)
    groups = [group for group in groups if group.get('name').startswith(prefix)]
    for group in groups:
        group = set_group_arguments(group, startdate) #Set the date etc
    return groups

def find_date(startdate, weekday, weeknumber):
    "Find the date that is the <weekday> of the <weeknumber> week after <date>. (See docs above)."
    #The +1 makes this match up with linux times (day 1 = Monday)
    daysahead = weekday - (startdate.weekday()+1)
    if daysahead < 0:
        #Target day already happened this week
        daysahead += 7
    #Add 7 days for each Week Of Month we want - but 'This' week is week 1
    daysahead += 7*(weeknumber-1)
    return startdate + datetime.timedelta(daysahead)

def next_month(startdate):
    "Find the start of the month after <workingdate>"
    if not startdate:
        startdate = datetime.datetime.now()
    startdate = startdate.replace(day=1)
    #If it's December then next month is January next year not month 13 of this year
    if startdate.month == 12:
        startdate = startdate.replace(month=1)
        startdate = startdate.replace(year=(startdate.year+1))
    else:
        startdate = startdate.replace(month=(startdate.month+1))
    return startdate

def set_group_arguments(group, startdate):
    "Set the date to schedule the work for"
    #We just want the arguments from the end of the description
    group['arguments'] = re.sub(r"^(.|\n)*###Args:", "", group.get('description'))
    arguments = re.split(" ", group['arguments'])
    arguments[2] = re.split(":", arguments[2])
    scheddate = next_month(startdate)
    scheddate = find_date(scheddate, int(arguments[0]), int(arguments[1]))
    arguments[2][0] = int(arguments[2][0])
    arguments[2][1] = int(arguments[2][1])
    if arguments[2][0] > 23:
        arguments[2][0] -= 24
        scheddate = scheddate + datetime.timedelta(days=1)
    scheddate = scheddate.replace(hour=int(arguments[2][0])).replace(minute=int(arguments[2][1]))
    group['schedule'] = scheddate
    group['reboot'] = "Always" if arguments[3] == "" else arguments[3]
    return group

def patch_groups():
    "Actually schedule the work for matching systems."
    #This file should be based on configuration.py.template
    import configuration as conf
    client = xmlrpclib.Server(conf.SATELLITE_URL, verbose=0)
    key = client.auth.login(conf.SATELLITE_LOGIN, conf.SATELLITE_PASSWORD)
    groups = get_groups(client, key, conf.PREFIX, conf.STARTDATE)
    for group in groups:
        systems = client.systemgroup.listSystemsMinimal(key, group['name'])
        for system in systems:
            tag_group_system(client, key, system['id'])
            schedule_pending_errata(client, key, system['id'], group['schedule'], group['reboot'])
    client.auth.logout(key)

patch_groups()
