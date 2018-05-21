"""
This will schedule autopatching for all systems in groups listed in listfile
This will be formatted:

<Group Name>,<DayOfWeek>,<Week Of Month>,<Time>,<RebootPlan>

The values are:
<String>,<0-7>,<1-4>,<00:00 - 47:59>,<Always|IfNeeded|Never>
    - DOW 0 is Sunday.
    - Week Of Month - 1 is the first week.    Values over 4 haven't been tested.
    - Time is in 24 hour time.  Hours over 23 will refer to hour-24 the next day.
    - RebootPlan:
        - Always - reboot everytime we patch.
        - Never - do not reboot.
        - IfNeeded - reboot if a reboot is needed, otherwise don't.
          **NOTE** This doesn't work yet as knowing when it is needed is hard.

The only configurable values are in configuration.py.
You should base configuration.py on configuration.py.template
"""


def tag_group_system(client, key, systemid, tagname=""):
    """This will tag the latest snapshot for a system with the name <tagname>"""
    import datetime
    tagname += datetime.datetime.now().strftime("%Y%m%d%H%M%S%f")
    snaplist = client.system.provisioning.snapshot.list_snapshots(key, systemid, {})
    client.system.provisioning.snapshot.addTagToSnapshot(key, snaplist[0].get('id'), tagname)


def schedule_pending_errata(client, key, system, date, reboot):
    """This will schedule an action chain of all outstanding errata for the system"""
    import datetime
    chainname = datetime.datetime.now().strftime("%Y%m%d%H%M%S%f") + str(system)
    errataset = client.system.getRelevantErrata(key, system)
    if errataset:
        earray = []
        # getRelevantErrata gives us an array of errata (which are arrays of errata details).
        # addErrataUpdate needs an array of errata ids
        for errata in errataset:
            earray.extend([int(errata.get('id'))])
        client.actionchain.createChain(key, chainname)
        client.actionchain.addErrataUpdate(key, system, earray, chainname)
        if reboot == "Always":
            client.actionchain.addSystemReboot(key, system, chainname)
        elif reboot == "IfNeeded":
            # Maybe one day we'll have more smarts in here, till then a reboot is always required
            client.actionchain.addSystemReboot(key, system, chainname)
        client.actionchain.scheduleChain(key, chainname, date)


def find_date(startdate, weekday, weeknumber):
    """Find the date that is the <weekday> of the <weeknumber> week after <date>. (See docs above)."""
    import datetime
    # The +1 makes this match up with linux times (day 1 = Monday)
    daysahead = weekday - (startdate.weekday() + 1)
    if daysahead < 0:
        # Target day already happened this week
        daysahead += 7
    # Add 7 days for each Week Of Month we want - but 'This' week is week 1
    daysahead += 7 * (weeknumber - 1)
    return startdate + datetime.timedelta(daysahead)


def next_month(startdate):
    """Find the start of the month after <workingdate>"""
    import datetime
    if not startdate:
        startdate = datetime.datetime.now()
    startdate = startdate.replace(day=1)
    # If it's December then next month is January next year not month 13 of this year
    if startdate.month == 12:
        startdate = startdate.replace(month=1)
        startdate = startdate.replace(year=(startdate.year + 1))
    else:
        startdate = startdate.replace(month=(startdate.month + 1))
    return startdate


def interpret_time(list_item, startdate=None):
    """Take the data we get from the CSV and turn it into a real date"""
    import re
    import datetime
    import configuration as conf
    if not startdate:
        startdate = conf.STARTDATE
    weekday = int(list_item[1])
    weeknumber = int(list_item[2])
    time = re.split(":", list_item[3])
    hours = int(time[0])
    minutes = int(time[1])
    if not startdate:
        startdate = datetime.datetime.now()
    # We always schedule at the end of the month, so lets reset to the start of next
    startdate = startdate.replace(day=1)
    # If it's December then next month is January next year not month 13 of this year
    if startdate.month == 12:
        startdate = startdate.replace(month=1)
        startdate = startdate.replace(year=(startdate.year + 1))
    else:
        startdate = startdate.replace(month=(startdate.month + 1))
    # Now we have a start date of the start of the month after that in startdate (normally today)
    # The +1 makes this match up with linux times (day 1 = Monday)
    daysahead = weekday - (startdate.weekday() + 1)
    if daysahead < 0:
        # Target day already happened this week
        daysahead += 7
    # Add 7 days for each Week Of Month we want - but 'This' week is week 1
    daysahead += 7 * (weeknumber - 1)
    schedule = startdate + datetime.timedelta(daysahead)
    # If the time is over 24 hours then we mean hours-24 the next day
    if hours > 23:
        hours -= 24
        schedule = schedule + datetime.timedelta(days=1)
    schedule = schedule.replace(hour=hours).replace(minute=minutes)
    return schedule


def process_list(listfile=None):
    """Process the list of tags and schedules"""
    import csv
    import xmlrpclib
    import configuration as conf
    if not listfile:
        listfile = conf.LISTFILE
    client = xmlrpclib.Server(conf.SATELLITE_URL, verbose=0)
    key = client.auth.login(conf.SATELLITE_LOGIN, conf.SATELLITE_PASSWORD)
    with open(listfile) as csvfile:
        filereader = csv.reader(csvfile)
        for row in filereader:
            schedule = interpret_time(row)
            systems = client.systemgroup.listSystemsMinimal(key, row[0])
            for system in systems:
                tag_group_system(client, key, system['id'])
                schedule_pending_errata(client, key, system['id'], schedule, row[4])
            client.auth.logout(key)


if __name__ == "__main__":
    process_list()
