#!/bin/bash

python database_scripts/cleanup.py -s
python database_scripts/populate.py --satellites --groundstations
./test_day-in-the-life.sh