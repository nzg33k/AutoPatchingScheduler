'''
This will autopatch machines using landscape
'''
#This file should be based on configuration.py.template
import csv
import re
import datetime
from landscape_api.base import API as landscape_api
import configuration as conf

def get_computers_by_tag(tag):
    "Get the computers with a specific tag"
    api = landscape_api(conf.uri, conf.key, conf.secret, conf.ca)
    computers = api.get_computers(query="tag:"+tag) # pylint: disable=no-member
    return computers

def upgrade_by_tag(tag, deliver_after, packages=None, security_only=False, deliver_delay_window=0):
    "Upgrade all systems with the given tag"
    if packages is None:
        packages = []
    api = landscape_api(conf.uri, conf.key, conf.secret, conf.ca)
    tag = "tag:"+tag
    result = api.upgrade_packages(tag, packages, security_only, deliver_after, deliver_delay_window) # pylint: disable=no-member
    return result

def interpret_time(list_item, startdate=conf.startdate):
    "Take the data we get from the CSV and turn it into a real date"
    weekday = int(list_item[1])
    weeknumber = int(list_item[2])
    time = re.split(":", list_item[3])
    hours = int(time[0])
    minutes = int(time[1])
    if not startdate:
        startdate = datetime.datetime.now()
    #We always schedule at the end of the month, so lets reset to the start of next
    startdate = startdate.replace(day=1)
    #If it's December then next month is January next year not month 13 of this year
    if startdate.month == 12:
        startdate = startdate.replace(month=1)
        startdate = startdate.replace(year=(startdate.year+1))
    else:
        startdate = startdate.replace(month=(startdate.month+1))
    #Now we have a start date of the start of the month after that in startdate (normally today)
    #The +1 makes this match up with linux times (day 1 = Monday)
    daysahead = weekday - (startdate.weekday()+1)
    if daysahead < 0:
        #Target day already happened this week
        daysahead += 7
    #Add 7 days for each Week Of Month we want - but 'This' week is week 1
    daysahead += 7*(weeknumber-1)
    schedule = startdate + datetime.timedelta(daysahead)
    #If the time is over 24 hours then we mean hours-24 the next day
    if hours > 23:
        hours -= 24
        schedule = schedule + datetime.timedelta(days=1)
    schedule = schedule.replace(hour=hours).replace(minute=minutes)
    return schedule

def reboot_by_tag(tag, schedule):
    "Reboot computers with this tag on this schedule"
    api = landscape_api(conf.uri, conf.key, conf.secret, conf.ca)
    api.reboot_computers(get_computers_by_tag(tag), schedule) # pylint: disable=no-member

def process_list(listfile=conf.listfile):
    "Process the list of tags and schedules"
    with open(listfile) as csvfile:
        filereader = csv.reader(csvfile)
        for row in filereader:
            schedule = interpret_time(row)
            #print schedule
            upgrade_by_tag(row[0], schedule)
            #We do not know when patching will be finished so this is not a good idea.
            #I have asked canonical for suggestions.
            #I will leave this commented out to play with later.
            #reboot_by_tag(row[0], schedule)

process_list()
#upgrade_by_tag("testapsw", "2018-03-13T13:30:00Z")
