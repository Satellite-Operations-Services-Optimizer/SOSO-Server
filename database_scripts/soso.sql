CREATE SCHEMA IF NOT EXISTS soso_schema;
SET SEARCH_PATH = soso_schema;

CREATE OR REPLACE FUNCTION set_default_name()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.name IS NULL THEN
        NEW.name := 'unnamed_' || TG_ARGV[0] || '_' || NEW.id;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ================== Schedule table ================
CREATE TABLE IF NOT EXISTS schedule (
	id integer PRIMARY KEY GENERATED BY DEFAULT AS IDENTITY,
	name text UNIQUE NOT NULL,
	group_name text DEFAULT NULL -- this is the group of schedules that are related to each other. e.g. schedules that all belong to the second generation of a genetic algorithm in a population of schedules
);

CREATE OR REPLACE TRIGGER schedule_default_name
BEFORE INSERT ON schedule
FOR EACH ROW
EXECUTE FUNCTION set_default_name('schedule');

INSERT INTO schedule (id, name, group_name) 
VALUES (0, 'Default Schedule', NULL) 
ON CONFLICT (id) -- TODO: handle case where we change the default name to some other name that already exists in the database. not important to handle anytime soon (or maybe even ever in our project tbh), but something to think about
DO UPDATE SET name = EXCLUDED.name, group_name = EXCLUDED.group_name;

-- schedule lock - for future stuff
CREATE EXTENSION IF NOT EXISTS btree_gist; -- required for the EXCLUDE constraint with range types
CREATE TABLE IF NOT EXISTS schedule_lock (
	id integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
	schedule_id integer REFERENCES schedule (id),
	acquisition_time timestamptz DEFAULT CURRENT_TIMESTAMP,
	time_range tstzrange,
	lock_priority integer DEFAULT 0 NOT NULL CHECK (lock_priority >= 0), -- priority would be based on "how many items do I need to schedule? if I need to schedule `delta` amount more than you, i don't care that you have the lock, I will steal the lock from you (delete conflicting row and insert new lock with higher priority)". maybe also consider the new things you will have to schedule that the previous lock owner was trying to schedule, that fall in teh overlap range
	EXCLUDE USING gist (schedule_id WITH =, time_range WITH &&)
);
-- ================== End of Schedule table ================


-- ================== Asset Tables ==================
CREATE TYPE asset_type AS ENUM ('satellite', 'groundstation');
CREATE TABLE IF NOT EXISTS asset (
	id integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
	name text UNIQUE NOT NULL,
	asset_type asset_type NOT NULL,
	schedule_id integer NOT NULL DEFAULT 0 REFERENCES schedule (id) -- default schedule has id 0. An asset can only belong to one schedule at a time
);

CREATE TABLE IF NOT EXISTS ground_station (
	id integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
	name text UNIQUE NOT NULL,
	latitude double precision,
	longitude double precision,
	elevation double precision,
	send_mask double precision,
	receive_mask double precision,
	uplink_rate_mbps double precision,
	downlink_rate_mbps double precision,
	schedule_id integer NOT NULL REFERENCES schedule (id),
	asset_type asset_type DEFAULT 'groundstation'::asset_type NOT NULL CHECK (asset_type = 'groundstation')
) INHERITS (asset);

CREATE OR REPLACE TRIGGER ground_station_default_name
BEFORE INSERT ON ground_station
FOR EACH ROW
EXECUTE FUNCTION set_default_name('ground_station');

CREATE TABLE IF NOT EXISTS satellite (
	id integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
	name text UNIQUE NOT NULL,
	tle json,
	storage_capacity double precision,
	power_capacity double precision,
	fov_max double precision,
	fov_min double precision,
	schedule_id integer NOT NULL REFERENCES schedule (id),
	asset_type asset_type DEFAULT 'satellite'::asset_type NOT NULL CHECK (asset_type = 'satellite')
) INHERITS (asset);

CREATE OR REPLACE TRIGGER satellite_default_name
BEFORE INSERT ON satellite
FOR EACH ROW
EXECUTE FUNCTION set_default_name('satellite');
-- ================== End of Asset Tables ==================

-- ================== Order Tables ==================
CREATE TYPE order_type AS ENUM ('imaging', 'maintenance', 'gs_outage', 'sat_outage');
-- abstract table. do not define constraints on this (including primary/foreign key constraints), as it won't be inherited by the children
CREATE TABLE IF NOT EXISTS system_order (
	id integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
	schedule_id integer NOT NULL DEFAULT 0 REFERENCES schedule (id), -- default schedule has id 0
	asset_id integer DEFAULT NULL, -- optional field. if null, then the order can be fulfilled by any asset
	start_time timestamptz NOT NULL, -- maybe rename to make it clear that it is not the actual start/end time of the event, but the window in which it can be scheduled
	end_time timestamptz NOT NULL,
	duration interval NOT NULL,
	delivery_deadline timestamptz,
	visit_count integer NOT NULL DEFAULT 1,
	revisit_frequency interval DEFAULT '0 days', -- if revisit_frequency is 0 days, then it is a one-time order
	revisit_frequency_max interval DEFAULT NULL,
	priority integer DEFAULT 1 NOT NULL CHECK (priority >= 0)
	CONSTRAINT valid_end_time CHECK (end_time >= start_time),
	CONSTRAINT valid_delivery_deadline CHECK (delivery_deadline >= end_time),
	CONSTRAINT valid_visit_count CHECK (visit_count>=0)
);

CREATE TABLE IF NOT EXISTS transmitted_order (
	id integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
	uplink_size double precision DEFAULT 0.001 NOT NULL, -- command to transmit to asset is 1KB TODO: replace with actual value in bytes
	downlink_size double precision DEFAULT 0.0 NOT NULL,
	CONSTRAINT valid_uplink_size CHECK (uplink_size >= 0),
	CONSTRAINT valid_downlink_size CHECK (downlink_size >= 0)
) INHERITS (system_order);

CREATE TYPE image_type AS ENUM ('low_res', 'medium_res', 'high_res');
CREATE TABLE IF NOT EXISTS image_order (
    id integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    schedule_id integer REFERENCES schedule (id),
    latitude double precision,
    longitude double precision,
    image_type image_type,
	duration interval NOT NULL,
	downlink_size double precision DEFAULT NULL NOT NULL, -- default is NULL so it is populated by the image order BEFPRE INSERT trigger
    order_type order_type DEFAULT 'imaging'::order_type NOT NULL,
	CONSTRAINT valid_order_type CHECK (order_type = 'imaging')
) INHERITS (transmitted_order);

CREATE OR REPLACE FUNCTION set_default_imaging_values()
RETURNS TRIGGER AS $$
BEGIN
	IF NEW.downlink_size IS NULL THEN
		CASE NEW.image_type 
			WHEN 'low_res' THEN 
				NEW.downlink_size := 128.0; -- size in MB
			WHEN 'medium_res' THEN 
				NEW.downlink_size := 256.0; -- size in MB
			WHEN 'high_res' THEN 
				NEW.downlink_size := 512.0; -- size in MB
		END CASE;
	END IF;
	IF NEW.duration IS NULL THEN
		CASE NEW.image_type 
			WHEN 'low_res' THEN 
				NEW.duration := '20 seconds'::interval;
			WHEN 'medium_res' THEN 
				NEW.duration := '45 seconds'::interval;
			WHEN 'high_res' THEN 
				NEW.duration := '120 seconds'::interval;
		END CASE;
	END IF;


	RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE TRIGGER set_default_imaging_values_trigger
BEFORE INSERT ON image_order
FOR EACH ROW
EXECUTE FUNCTION set_default_imaging_values();

CREATE TABLE IF NOT EXISTS maintenance_order (
	id integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
	schedule_id integer REFERENCES schedule (id),
	operations_flag boolean,
	description text,
	order_type order_type DEFAULT 'maintenance'::order_type NOT NULL,
	asset_id integer NOT NULL REFERENCES satellite (id), -- maintenance orders must be performed on a specific asset. TODO: My assumption is that we don't have maintenance orders for groundstations. veryfy with tsa.
	CONSTRAINT valid_order_type CHECK (order_type = 'maintenance')
) INHERITS (transmitted_order);

-- abstract table. do not define constraints on this (including primary/foreign key constraints), as it won't be inherited by the children
CREATE TABLE IF NOT EXISTS outage_order (
	id integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
	schedule_id integer REFERENCES schedule (id),
	order_type order_type,
	asset_id integer NOT NULL -- outage orders must be performed on a specific asset, whether satellite or groundstation
	CONSTRAINT valid_order_type CHECK (order_type = 'gs_outage' OR order_type = 'sat_outage')
) INHERITS (system_order);

CREATE TABLE IF NOT EXISTS groundstation_outage_order (
	id integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
	schedule_id integer REFERENCES schedule (id),
	order_type order_type DEFAULT 'gs_outage'::order_type NOT NULL,
	asset_id integer NOT NULL REFERENCES ground_station (id) CHECK (order_type = 'gs_outage')
) INHERITS (outage_order);

CREATE INDEX IF NOT EXISTS groundstation_outage_order_start_time_index ON groundstation_outage_order (start_time);
CREATE INDEX IF NOT EXISTS groundstation_outage_order_end_time_index ON groundstation_outage_order (end_time);

CREATE TABLE IF NOT EXISTS satellite_outage_order (
	id integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
	schedule_id integer REFERENCES schedule (id),
	order_type order_type DEFAULT 'sat_outage'::order_type NOT NULL,
	asset_id integer NOT NULL REFERENCES satellite (id) CHECK (order_type = 'sat_outage')
) INHERITS (outage_order);

CREATE INDEX IF NOT EXISTS satellite_outage_order_start_time_index ON satellite_outage_order (start_time);
CREATE INDEX IF NOT EXISTS satellite_outage_order_end_time_index ON satellite_outage_order (end_time);

-- TODO: This table might need rethinking
CREATE TABLE IF NOT EXISTS ground_station_request (
	id integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
	schedule_id integer NOT NULL REFERENCES schedule (id),
	station_id integer NOT NULL REFERENCES ground_station (id),
	signal_acquisition_time timestamp with time zone,
	signal_loss_time timestamp with time zone
);

CREATE INDEX IF NOT EXISTS ground_station_request_signal_acquisition_index ON ground_station_request (signal_acquisition_time);
CREATE INDEX IF NOT EXISTS ground_station_request_signal_loss_index ON ground_station_request (signal_loss_time);

CREATE TYPE schedule_request_status AS ENUM ('received', 'processing', 'scheduled', 'rejected');
CREATE TABLE IF NOT EXISTS schedule_request (
	id integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
	schedule_id integer NOT NULL REFERENCES schedule (id),
	order_id integer,
	order_type order_type, -- needed because order_id is not unique across the different order types
	asset_id integer DEFAULT NULL, -- it is null in the case where we don't care what asset it is performed on
	window_start timestamptz,
	window_end timestamptz CHECK (window_end >= window_start),
	duration interval NOT NULL,
	delivery_deadline timestamptz CHECK (delivery_deadline >= window_end), -- can be null if there is nothing to be delivered back, e.g. it is null for maintenance requests
	uplink_size double precision NOT NULL CHECK (uplink_size >= 0), -- there are some things we don't uplink/downlink, they will just have the default value of 0 for their uplink/downlink data size
	downlink_size double precision NOT NULL CHECK (downlink_size >= 0),
	priority integer DEFAULT 1 NOT NULL CHECK (priority >= 0) ,
	-- autogenerated, don't worry about this
	status schedule_request_status DEFAULT 'received'::schedule_request_status NOT NULL,
	requested_at timestamptz DEFAULT current_timestamp,
	UNIQUE (order_type, order_id, window_start)
);


CREATE TYPE event_type AS ENUM ('imaging', 'maintenance', 'gs_outage', 'sat_outage', 'contact', 'eclipse');

-- ================== Abstract tables for Scheduled Events ==================
-- NOTE: Do not define constraints on these tables (including primary/foreign key constraints), as it won't be inherited by the children
CREATE TABLE IF NOT EXISTS scheduled_event (
	id integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
	schedule_id integer NOT NULL DEFAULT 0, -- this is the schedule we are in the process of constructing. default schedule has id 0
	asset_id integer NOT NULL, -- this is the resource we are scheduling to.
	start_time timestamptz NOT NULL,
	duration interval NOT NULL,
	window_start timestamptz DEFAULT NULL CHECK (window_start <= start_time), -- this is the start of the buffer zone. it is the earliest time this event can be shifted to
	window_end timestamptz DEFAULT NULL CHECK (window_end >= start_time+duration),
	-- these fields are auto-generated always
	event_type event_type NOT NULL,
	asset_type asset_type NOT NULL
);

CREATE TABLE IF NOT EXISTS windowed_time_event (
	id integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
	window_start timestamptz NOT NULL,
	window_end timestamptz NOT NULL
) INHERITS (scheduled_event);

CREATE OR REPLACE FUNCTION set_default_window_time()
RETURNS TRIGGER AS $$
BEGIN
	IF NEW.window_start IS NULL THEN
		NEW.window_start := NEW.start_time;
	END IF;
	IF NEW.window_end IS NULL THEN
		NEW.window_end := NEW.start_time + NEW.duration;
	END IF;
	RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE TRIGGER set_default_window_time_trigger
BEFORE INSERT ON windowed_time_event
FOR EACH ROW
EXECUTE FUNCTION set_default_window_time();

CREATE TABLE IF NOT EXISTS fixed_time_event (
	id integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
 	window_start timestamptz DEFAULT NULL CHECK (window_start IS NULL),
 	window_end timestamptz DEFAULT NULL CHECK (window_start IS NULL)
) INHERITS (scheduled_event);
-- ================== End of Abstract tables for Scheduled Events ==================

CREATE TABLE IF NOT EXISTS scheduled_contact (
	id integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
	schedule_id integer REFERENCES schedule (id),
	asset_id integer REFERENCES satellite (id),
	groundstation_id integer REFERENCES ground_station (id),
	-- the fields below are autogenerated by the database. don't worry about them.
	event_type event_type DEFAULT 'contact'::event_type NOT NULL CHECK (event_type = 'contact'),
	asset_type asset_type DEFAULT 'satellite'::asset_type NOT NULL CHECK (asset_type = 'satellite')
) INHERITS (fixed_time_event);

CREATE INDEX IF NOT EXISTS scheduled_contact_start_time_index ON scheduled_contact (start_time);
CREATE INDEX IF NOT EXISTS scheduled_contact_asset_index ON scheduled_contact (asset_id);

CREATE TABLE IF NOT EXISTS scheduled_outage (
	id integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY
) INHERITS (fixed_time_event);

CREATE TABLE IF NOT EXISTS groundstation_outage (
	id integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
	schedule_id integer REFERENCES schedule (id),
	asset_id integer REFERENCES ground_station(id),
	request_id integer NOT NULL REFERENCES schedule_request(id),
	-- the fields below are autogenerated by the database. don't worry about them.
	event_type event_type DEFAULT 'gs_outage'::event_type NOT NULL CHECK (event_type = 'gs_outage'),
	asset_type asset_type DEFAULT 'groundstation'::asset_type NOT NULL CHECK (asset_type = 'groundstation')
) INHERITS (scheduled_outage);

CREATE INDEX IF NOT EXISTS groundstation_outage_start_time_index ON groundstation_outage (start_time);
CREATE INDEX IF NOT EXISTS groundstation_outage_asset_index ON groundstation_outage (asset_id);

CREATE TABLE IF NOT EXISTS satellite_outage (
	id integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
	schedule_id integer REFERENCES satellite (id),
	asset_id integer REFERENCES satellite (id),
	request_id integer NOT NULL REFERENCES schedule_request (id),
	-- the fields below are autogenerated by the database. don't worry about them.
	event_type event_type DEFAULT 'sat_outage'::event_type NOT NULL CHECK (event_type = 'sat_outage'),
	asset_type asset_type DEFAULT 'satellite'::asset_type NOT NULL CHECK (asset_type = 'satellite')
) INHERITS (scheduled_outage);

CREATE INDEX IF NOT EXISTS satellite_outage_start_time_index ON satellite_outage (start_time);
CREATE INDEX IF NOT EXISTS satellite_outage_asset_index ON satellite_outage (asset_id);

CREATE TABLE IF NOT EXISTS satellite_eclipse(
	id integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
	schedule_id integer REFERENCES schedule (id),
	asset_id integer REFERENCES satellite (id),
	-- the fields below are autogenerated by the database. don't worry about them.
	event_type event_type DEFAULT 'eclipse'::event_type NOT NULL CHECK (event_type = 'eclipse'),
	asset_type asset_type DEFAULT 'satellite'::asset_type NOT NULL CHECK (asset_type = 'satellite')
) INHERITS (fixed_time_event);

CREATE INDEX IF NOT EXISTS satellite_eclipse_start_time_index ON satellite_eclipse (start_time);
CREATE INDEX IF NOT EXISTS satellite_eclipse_asset_index ON satellite_eclipse (asset_id);

-- abstract table. do not define constraints on this (including primary/foreign key constraints), as it won't be inherited by the children
CREATE TABLE IF NOT EXISTS transmitted_event (
	id integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
	schedule_id integer REFERENCES schedule (id),
	asset_id integer REFERENCES satellite (id),
	request_id integer NOT NULL REFERENCES schedule_request(id),
	uplink_contact_id integer NOT NULL REFERENCES scheduled_contact (id),
	downlink_contact_id integer DEFAULT NULL REFERENCES scheduled_contact (id), -- it is nullable because not all events have data they have to transmit back to groundstation
	uplink_size double precision NOT NULL CHECK (uplink_size>=0),
	downlink_size double precision NOT NULL CHECK (downlink_size>=0),
	priority integer NOT NULL CHECK (priority>=0), -- used to calculate throughput
	-- the fields below are autogenerated by the database. don't worry about them.
	asset_type asset_type DEFAULT 'satellite'::asset_type NOT NULL CHECK (asset_type = 'satellite')
) INHERITS (windowed_time_event);

CREATE INDEX IF NOT EXISTS transmitted_event_start_time_index ON transmitted_event (start_time);
CREATE INDEX IF NOT EXISTS transmitted_event_asset_index ON transmitted_event (asset_id);
CREATE INDEX IF NOT EXISTS transmitted_event_schedule_index ON transmitted_event (schedule_id);
CREATE INDEX IF NOT EXISTS transmitted_event_type_index ON transmitted_event (event_type);

CREATE TABLE IF NOT EXISTS scheduled_imaging (
	id integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
	schedule_id integer REFERENCES schedule (id),
	asset_id integer REFERENCES satellite (id),
	request_id integer NOT NULL REFERENCES schedule_request(id),
	uplink_contact_id integer NOT NULL REFERENCES scheduled_contact (id),
	downlink_contact_id integer DEFAULT NULL REFERENCES scheduled_contact (id), -- it is nullable because not all events have data they have to transmit back to groundstation
	-- the fields below are autogenerated by the database. don't worry about them.
	event_type event_type DEFAULT 'imaging'::event_type NOT NULL CHECK (event_type = 'imaging')
) INHERITS (transmitted_event);

CREATE TABLE IF NOT EXISTS scheduled_maintenance (
	id integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
	schedule_id integer REFERENCES schedule (id),
	asset_id integer REFERENCES satellite (id),
	request_id integer NOT NULL REFERENCES schedule_request(id),
	uplink_contact_id integer NOT NULL REFERENCES scheduled_contact (id),
	downlink_contact_id integer DEFAULT NULL REFERENCES scheduled_contact (id), -- it is nullable because not all events have data they have to transmit back to groundstation
	-- the fields below are autogenerated by the database. don't worry about them.
	event_type event_type DEFAULT 'maintenance'::event_type NOT NULL CHECK (event_type = 'maintenance')
) INHERITS (transmitted_event);

CREATE VIEW eventwise_asset_state_change AS
	-- Three cases where the satellite's state changes. (calculate your state_delta in it's respective case, and leave it as 0)
	-- CASE 1: when we are uplinking the command (e.g. command to take image is uplinked)
	SELECT transmitted_event.schedule_id,
		transmitted_event.asset_id,
		transmitted_event.asset_type,
		contact.start_time as snapshot_time, -- state changes at point of contact (when uplink actually occurs)
		transmitted_event.uplink_size as storage_delta,
		0 as throughput_delta
	FROM transmitted_event, scheduled_contact as contact
	WHERE transmitted_event.schedule_id=contact.schedule_id
		AND transmitted_event.asset_id=contact.asset_id
		AND transmitted_event.uplink_contact_id=contact.id
	UNION ALL
	-- CASE 2: when the command is executed (e.g. image is taken)
	SELECT transmitted_event.schedule_id,
		transmitted_event.asset_id,
		transmitted_event.asset_type,
		transmitted_event.start_time as snapshot_time, -- state changes at point of execution (when the event is actually scheduled to happen on the satellite)
		transmitted_event.downlink_size - transmitted_event.uplink_size as storage_delta, -- the command data that was uplinked can be deleted now as the command has been executed. The result of the command now takes up space.
		transmitted_event.priority as throughput_delta
	FROM transmitted_event
	WHERE transmitted_event.downlink_contact_id IS NOT NULL
	UNION ALL
	-- CASE 3: when the result of the command is being downlinked (e.g. image is being downlinked)
	SELECT transmitted_event.schedule_id,
		transmitted_event.asset_id,
		transmitted_event.asset_type,
		contact.start_time as snapshot_time, -- state changes at point of contact (when downlink actually occurs. we arbitrarily chose downlink_start_time instead of downlink_end_time. which is better to use is debatable, i can't think of a strong enough reason as to why one way and not the other)
		(-1.0)*transmitted_event.downlink_size as storage_delta,
		0 as throughput_delta
	FROM transmitted_event, scheduled_contact as contact
	WHERE transmitted_event.schedule_id=contact.schedule_id
		AND transmitted_event.asset_id=contact.asset_id
		AND transmitted_event.downlink_contact_id=contact.id;
		-- TODO: union changes corresponding to groundstation eventwise state changes

CREATE VIEW satellite_state_change AS
SELECT event_change.schedule_id, 
	event_change.asset_id, 
	event_change.asset_type,
	snapshot_time, 
	sum(storage_delta) /* / storage_capacity -- (divide by storage capacity, commented out because capacity too large) */ as storage_util_delta, -- this sum accounts for the case where multiple events are scheduled for the same time that have effect on the load
	-- TODO: Handle power usage (involves eclipses)
	sum(throughput_delta) as throughput_delta
FROM eventwise_asset_state_change as event_change, satellite
WHERE event_change.asset_id=satellite.id
	AND event_change.asset_type='satellite'::asset_type
	AND (storage_delta <> 0 OR throughput_delta <> 0)-- ignore cases where no change to the state
GROUP BY event_change.schedule_id, event_change.asset_type, event_change.asset_id, snapshot_time, storage_capacity; -- aggregate changes to the load made at the same time into one change

-- CREATE INDEX IF NOT EXISTS snapshot_time_index ON satellite_state_change (snapshot_time);
-- CREATE INDEX IF NOT EXISTS satellite_schedule_index ON satellite_state_change (schedule_id, satellite_id);
-- CREATE INDEX IF NOT EXISTS schedule_index ON satellite_state_change (schedule_id); -- useful when calculating average satellite utilization for example - you want events for all satellites within the same schedule


CREATE VIEW ground_station_state_change AS
SELECT event_change.schedule_id,
	event_change.asset_id, 
	event_change.asset_type,
	snapshot_time
FROM eventwise_asset_state_change as event_change, ground_station
WHERE event_change.asset_id=ground_station.id
	AND event_change.asset_type='groundstation'::asset_type
GROUP BY event_change.schedule_id, event_change.asset_type, event_change.asset_id, snapshot_time;