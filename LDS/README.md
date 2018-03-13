# AutoPatchingScheduler IN DEVELOPMENT

Setup is pretty easy:
1. Get the api.py
2. Create a configuration.py based on configuration.py.template
3. Setup the csv file
4. Run!

The CSV file must be in the right format:

    <tag name>,<DayOfWeek>,<Week Of Month>,<Time>

The values are:

    <String>,<0-7>,<1-4>,<00:00 - 47:59>
    
   - tag name should match a tag in landscape.
   - DOW 0 is Sunday.
   - Week Of Month - 1 is the first week.    Values over 4 haven't been tested.
   - Time is in 24 hour time.  Hours over 23 will refer to hour-24 the next day.
   
https://landscape.canonical.com/static/doc/api/
