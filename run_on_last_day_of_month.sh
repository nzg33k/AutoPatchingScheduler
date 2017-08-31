#!/bin/bash

[ "$(date +%d -d 'tomorrow')" == "01" ] && python `dirname $0`/api.py
