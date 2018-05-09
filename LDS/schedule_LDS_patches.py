"""
This will autopatch machines using landscape

Todo:
  Look at ways to make systems patched at different times get the same packages.
  Manage reboots - canonical suggest polling for the need reboot flag (yuck)

The configuration.py file should be a copy of configuration.py.template
The copy should have the details (key, secret etc) filled in.

The CSV file should be based on the template too, and should be formatted:
  <tag name>,<DayOfWeek>,<Week Of Month>,<Time>
  <String>,<0-7>,<1-4>,<00:00 - 47:59>
  - tag name should match a tag in landscape.
  - DOW 0 is Sunday.
  - Week Of Month - 1 is the first week. Values over 4 haven't been tested.
  - Time is in 24 hour time. Hours over 23 will refer to hour-24 the next day.

"""
import csv
import re
import datetime
import dateutil.relativedelta as relativedelta
from landscape_api.base import API as landscape_api
# This file should be based on configuration.py.template
import configuration as conf


def get_computers_by_tag(tag):
    """Get the computers with a specific tag"""
    api = landscape_api(conf.LDS_URI, conf.LDS_KEY, conf.LDS_SECRET, conf.LDS_CA)
    computers = api.get_computers(query="tag:" + tag)  # pylint: disable=no-member
    return computers


def upgrade_by_tag(tag, deliver_after, packages=None, security_only=False, deliver_delay_window=0):
    """Upgrade all systems with the given tag"""
    if packages is None:
        packages = []
    api = landscape_api(conf.LDS_URI, conf.LDS_KEY, conf.LDS_SECRET, conf.LDS_CA)
    tag = "tag:" + tag
    result = api.upgrade_packages(tag, packages, security_only, deliver_after,
                                  deliver_delay_window)  # pylint: disable=no-member
    return result


def interpret_time(list_item, startdate=conf.STARTDATE):
    """Take the data we get from the CSV and turn it into a real date"""
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


def reboot_by_tag(tag, schedule):
    """Reboot computers with this tag on this schedule"""
    api = landscape_api(conf.LDS_URI, conf.LDS_KEY, conf.LDS_SECRET, conf.LDS_CA)
    computerlist = get_computers_by_tag(tag)
    computers = []
    for computer in computerlist:
        computers.append(int(computer["id"]))
    api.reboot_computers(computers, schedule)  # pylint: disable=no-member


def process_list(listfile=conf.LISTFILE):
    """Process the list of tags and schedules"""
    with open(listfile) as csvfile:
        filereader = csv.reader(csvfile)
        for row in filereader:
            if get_computers_by_tag(row[0]) != []:
                schedule = interpret_time(row)
                rebootschedule = schedule + relativedelta.relativedelta(hours=2)
                upgrade_by_tag(row[0], schedule)
                reboot_by_tag(row[0], rebootschedule)


if __name__ == "__main__":
    process_list()
