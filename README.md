# AutoPatchingScheduler

Setup is pretty easy:
1. Get the api.py
2. Create a configuration.py based on configuration.py.template
3. Run!

We depend on the prefix being set and the matching group descriptions ending in the right format:

    ###Args:<DayOfWeek> <Week Of Month> <Time> <RebootPlan>

The values are:

    ###Args:<0-7> <1-4> <00:00 - 47:59> <Always|IfNeeded|Never>
    
   - DOW 0 is Sunday.
   - Week Of Month - 1 is the first week.    Values over 4 haven't been tested.
   - Time is in 24 hour time.  Hours over 23 will refer to hour-24 the next day.
   - RebootPlan:
        - 'Always' - reboot everytime we patch.
        - 'Never' - do not reboot.
        - 'IfNeeded' - reboot if a reboot is needed, otherwise don't.
           **NOTE** This doesn't work yet as knowing when it is needed is hard.


http://spacewalk.redhat.com/documentation/api/2.6/index.html has a good API overview which helped a lot in writing this.
