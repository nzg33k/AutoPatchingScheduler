#!/bin/bash

#You should call this from cron, something like 
#1  0 28-31 * * /path/to/run_on_last_day_of_month.sh

[ "$(date +%d -d 'tomorrow')" == "01" ] && pushd `dirname $0` > /dev/null && python schedule_RHS5_patches.py && popd > /dev/null