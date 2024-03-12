#!/bin/bash

pip install -r requirements.txt 
pip install -r scheduler_service/requirements.txt

python app_config/scripts/add_config_to_python_path.py 

# Step 0: Cleanup and set reference time
clear
echo "Running the day-in-the-life (DITL) test" | tee day-in-the-life.log
echo "Step 0: Cleanup database and set schedule reference time to 2022-09-01T00:00:00" | tee -a day-in-the-life.log
python database_scripts/cleanup.py --schema --reference-time "2022-09-01T00:00:00" > /dev/null 2>&1
python database_scripts/populate.py --satellites --groundstations > /dev/null 2>&1

SCHEDULER_STARTUP_WAIT_TIME=0
# Step 1
echo "Step 1: Ingest all Batch 1 orders and all maintenance orders except for OrbitMaintenance6 and OrbitMaintenance7" | tee -a day-in-the-life.log
echo "populating..."
python database_scripts/populate.py --imaging database_scripts/sample_data/DITL1/Batch1/JSON --maintenance database_scripts/sample_data/DITL1/MaintenanceOrders/Batch1/ > /dev/null 2>&1
echo "All orders have been ingested. Starting scheduler timer..."
sleep $SCHEDULER_STARTUP_WAIT_TIME
echo "started scheduler timer. waiting for all schedule requests to be processed..."
python scheduler_service/tests/start_scheduler_timer.py | tee -a day-in-the-life.log

# Step 2
echo "Step 2: Ingest all Batch 2 orders" | tee -a day-in-the-life.log
echo "populating..."
python database_scripts/populate.py --imaging database_scripts/sample_data/DITL1/Batch2/JSON > /dev/null 2>&1
echo "All orders have been ingested. Starting scheduler timer..."
sleep $SCHEDULER_STARTUP_WAIT_TIME
echo "started scheduler timer. waiting for all schedule requests to be processed..."
python scheduler_service/tests/start_scheduler_timer.py | tee -a day-in-the-life.log

# Step 3
echo "Step 3: Ingest all Batch 3 orders" | tee -a day-in-the-life.log
echo "populating..."
python database_scripts/populate.py --imaging database_scripts/sample_data/DITL1/Batch3/JSON > /dev/null 2>&1
echo "All orders have been ingested. Starting scheduler timer..."
sleep $SCHEDULER_STARTUP_WAIT_TIME
echo "started scheduler timer. waiting for all schedule requests to be processed..."
python scheduler_service/tests/start_scheduler_timer.py | tee -a day-in-the-life.log

# Step 4
echo "Step 4: Ingest outage for GATN and SOSO-3" | tee -a day-in-the-life.log
echo "populating..."
python database_scripts/populate.py --outages database_scripts/sample_data/DITL1/Outage/ > /dev/null 2>&1
echo "All orders have been ingested. Starting scheduler timer..."
sleep $SCHEDULER_STARTUP_WAIT_TIME
echo "started scheduler timer. waiting for all schedule requests to be processed..."
python scheduler_service/tests/start_scheduler_timer.py | tee -a day-in-the-life.log

# Step 5
echo "Step 5: Ingest all Batch 4 orders" | tee -a day-in-the-life.log
echo "populating..."
python database_scripts/populate.py --imaging database_scripts/sample_data/DITL1/Batch4/JSON > /dev/null 2>&1
echo "All orders have been ingested. Starting scheduler timer..."
sleep $SCHEDULER_STARTUP_WAIT_TIME
echo "started scheduler timer. waiting for all schedule requests to be processed..."
python scheduler_service/tests/start_scheduler_timer.py | tee -a day-in-the-life.log

# Step 6
echo "Step 6: Ingest all Batch 5 orders" | tee -a day-in-the-life.log
echo "populating..."
python database_scripts/populate.py --imaging database_scripts/sample_data/DITL1/Batch5/JSON > /dev/null 2>&1
echo "All orders have been ingested. Starting scheduler timer..."
sleep $SCHEDULER_STARTUP_WAIT_TIME
echo "started scheduler timer. waiting for all schedule requests to be processed..."
python scheduler_service/tests/start_scheduler_timer.py | tee -a day-in-the-life.log

# Step 7
echo "Step 7: Ingest OrbitMaintenance6 and OrbitMaintenance7" | tee -a day-in-the-life.log
echo "populating..."
python database_scripts/populate.py --maintenance database_scripts/sample_data/DITL1/MaintenanceOrders/Batch2/
echo "All orders have been ingested. Starting scheduler timer..."
sleep $SCHEDULER_STARTUP_WAIT_TIME
echo "started scheduler timer. waiting for all schedule requests to be processed..."
python scheduler_service/tests/start_scheduler_timer.py | tee -a day-in-the-life.log
