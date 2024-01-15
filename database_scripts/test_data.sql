-- Insert Statements: Adds sample data to populate the tables
-- Ground Station
INSERT INTO "soso_schema"."ground_station" ("name", "latitude", "longitude", "elevation", "station_mask", "uplink_rate", "downlink_rate", "under_outage")
VALUES
    ('Inuvik', 68.3195, -133.549, 102.5, 5, 40000, 100000000, false)
    ,('Prince Albert', 53.2124, -105.934, 490.3, 5, 40000, 100000000, false)
    ,('Gatineau', 45.5846, -75.8083, 240.1, 5, 40000, 100000000, false);

-- Satellite
INSERT INTO "soso_schema"."satellite" ("name", "tle", "storage_capacity", "power_capacity", "fov_max", "fov_min", "is_illuminated", "under_outage")
VALUES
    ('Satellite1', '{"line1": "TLE_LINE_1", "line2": "TLE_LINE_2"}', 5000, 1000, 60, 30, true, false),
    ('Satellite2', '{"line1": "TLE_LINE_3", "line2": "TLE_LINE_4"}', 8000, 1200, 75, 45, false, false);

-- Schedule (edit value of satellite_id and ground_station_id)
INSERT INTO "soso_schema"."schedule" ("satellite_id", "ground_station_id", "asset_type", "start_time", "end_time", "status")
VALUES
    (1, 1, 1, '2023-11-20 12:00:00', '2023-11-20 14:00:00', 'Scheduled'),
    (2, 2, 2, '2023-11-21 08:00:00', '2023-11-21 10:00:00', 'Completed');

-- Image Order
INSERT INTO "soso_schema"."image_order" ("latitude", "longitude", "priority", "image_res", "image_height", "image_width", "start_time", "end_time", "delivery_deadline", "retake_count", "retake_freq_min", "retake_freq_max") 
VALUES 
    (25.0, -75.0, 3, 800, 600, 1200, '2023-01-11 14:00:00', '2023-01-11 15:00:00', '2023-01-11 17:00:00', 1, 30, 60),
    (35.0, -110.0, 2, 1200, 900, 1600, '2023-01-12 09:00:00', '2023-01-12 10:00:00', '2023-01-12 11:00:00', 2, 45, 90);

-- Test Queries: Selects data from different tables to verify the initial state
-- Ground Station
SELECT * FROM "soso_schema"."ground_station";
-- Satellite
SELECT * FROM "soso_schema"."satellite";
-- Schedule
SELECT * FROM "soso_schema"."schedule";
-- Image Order
SELECT * FROM "soso_schema"."image_order";

-- Insert Additional Data: Adds more sample data to test insert operations
-- Maintenance Order
INSERT INTO "soso_schema"."maintenance_order" ("asset_name", "start_time", "end_time", "duration", "repetition", "frequency_max", "frequency_min", "operations_flag", "description") 
VALUES 
    ('Asset1', '2023-01-14 08:00:00', '2023-01-14 12:00:00', '04:00:00', 2, 10, 5, true, 'Routine maintenance'),
    ('Asset2', '2023-01-15 10:00:00', '2023-01-15 15:00:00', '05:00:00', 1, 15, 10, false, 'Emergency maintenance');

-- Outage Order
INSERT INTO "soso_schema"."outage_order" ("asset_name", "start_time", "end_time") 
VALUES 
    ('Asset1', '2023-01-17 08:00:00', '2023-01-17 10:00:00'),
    ('Asset2', '2023-01-18 14:00:00', '2023-01-18 16:00:00');

-- Ground Station Request
INSERT INTO "soso_schema"."ground_station_request" ("schedule_id", "station_id", "signal_acquisition", "signal_loss") 
VALUES 
    (1, 1, '2023-01-10 10:00:00', '2023-01-10 11:00:00'),
    (2, 2, '2023-01-11 14:30:00', '2023-01-11 14:45:00');

-- Scheduled Images
INSERT INTO "soso_schema"."scheduled_images" ("schedule_id", "image_id", "request_id", "downlink_start", "downlink_end", "data_size", "schedule_type", "status") 
VALUES 
   (1, 1, 1, '2023-01-10 11:30:00', '2023-01-10 12:30:00', 500.0, 1, 'Success'),
   (2, 2, 2, '2023-01-11 15:15:00', '2023-01-11 16:00:00', 800.0, 2, 'Success');

-- Scheduled Maintenance
INSERT INTO "soso_schema"."scheduled_maintenance" ("schedule_id", "maintenance_id", "maintenance_start", "maintenance_end", "repetition_number", "description", "priority", "status") 
VALUES 
   (4, 1, '2023-01-14 08:00:00', '2023-01-14 12:00:00', 1, 'Routine maintenance', 2, 'Scheduled'),
   (5, 2, '2023-01-15 10:30:00', '2023-01-15 15:30:00', 2, 'Emergency maintenance', 1, 'Completed');

-- Scheduled Outages
INSERT INTO "soso_schema"."scheduled_outages" ("schedule_id", "outage_id", "outage_start", "outage_end", "status") 
VALUES 
   (7, 1, '2023-01-17 08:00:00', '2023-01-17 10:00:00', 'Scheduled'),
   (8, 2, '2023-01-18 14:30:00', '2023-01-18 16:30:00', 'Completed');

-- Update Statements: Modifies existing data to simulate updates
-- Ground Station
UPDATE "soso_schema"."ground_station" SET "latitude" = 40.0 WHERE "id" = 1;
-- Satellite
UPDATE "soso_schema"."satellite" SET "power_capacity" = 700.0 WHERE "id" = 2;
-- Schedule
UPDATE "soso_schema"."schedule" SET "status" = 'Canceled' WHERE "id" = 1;
-- Image Order
UPDATE "soso_schema"."image_order" SET "priority" = 4 WHERE "id" = 2;
-- Maintenance Order
UPDATE "soso_schema"."maintenance_order" SET "description" = 'Updated maintenance description' WHERE "id" = 1;
-- Outage Order
UPDATE "soso_schema"."outage_order" SET "end_time" = '2023-01-17 11:00:00' WHERE "id" = 1;
-- Ground Station Request
UPDATE "soso_schema"."ground_station_request" SET "signal_loss" = '2023-01-10 11:30:00' WHERE "id" = 1;
-- Scheduled Images
UPDATE "soso_schema"."scheduled_images" SET "status" = 'Failed' WHERE "id" = 2;
-- Scheduled Maintenance
UPDATE "soso_schema"."scheduled_maintenance" SET "status" = 'Completed' WHERE "id" = 2;
-- Scheduled Outages
UPDATE "soso_schema"."scheduled_outages" SET "status" = 'Completed' WHERE "id" = 2;

-- Delete Statements: Removes data to simulate deletions
-- Ground Station
DELETE FROM "soso_schema"."ground_station" WHERE "id" = 1;
-- Satellite
DELETE FROM "soso_schema"."satellite" WHERE "id" = 2;
-- Schedule
DELETE FROM "soso_schema"."schedule" WHERE "id" = 2;
-- Image Order
DELETE FROM "soso_schema"."image_order" WHERE "id" = 2;
-- Maintenance Order
DELETE FROM "soso_schema"."maintenance_order" WHERE "id" = 1;
-- Outage Order
DELETE FROM "soso_schema"."outage_order" WHERE "id" = 2;
-- Ground Station Request
DELETE FROM "soso_schema"."ground_station_request" WHERE "id" = 1;
-- Scheduled Images
DELETE FROM "soso_schema"."scheduled_images" WHERE "id" = 2;
-- Scheduled Maintenance
DELETE FROM "soso_schema"."scheduled_maintenance" WHERE "id" = 2;
-- Scheduled Outages
DELETE FROM "soso_schema"."scheduled_outages" WHERE "id" = 2;
