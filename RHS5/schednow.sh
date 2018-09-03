#!/bin/bash

echo "If you hit enter I will schedule everything for this month.  If some of these events should have happened earlier in the month then these will happen NOW."
echo "If you are ABSOLUTELY sure you want to continue, type 'I am sure' and press enter, otherwise just hit enter"
read RESPONSE
if [ "$RESPONSE" = "I am sure" ]
then
        echo "Ok, if you insist..."
        pushd `dirname $0` > /dev/null
        sed -i 's/^STARTDATE/#STARTDATE/g;s/^# STARTDATE/STARTDATE/g;' configuration.py
        python schedule_RHS5_patches.py
        sed -i 's/^STARTDATE/# STARTDATE/g;s/^#STARTDATE/STARTDATE/g;' configuration.py
        popd > /dev/null
else
        echo "Wise choice!"
fi