CREATE SCHEMA IF NOT EXISTS soso_schema;

SET SEARCH_PATH = soso_schema;

CREATE TABLE IF NOT EXISTS ground_station (
	id integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
	name text UNIQUE,
	latitude double precision,
	longitude double precision,
	elevation double precision,
	send_mask double precision,
	receive_mask double precision,
	uplink_rate_bps integer,
	downlink_rate_bps integer
);

CREATE TABLE IF NOT EXISTS satellite (
	id integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
	name text UNIQUE,
	tle json,
	storage_capacity double precision,
	power_capacity double precision,
	fov_max double precision,
	fov_min double precision
);

CREATE TABLE IF NOT EXISTS schedule_blueprint (
	id integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
	group_name integer DEFAULT NULL -- this is the group of schedules that are related to each other. e.g. schedules that all belong to the second generation of a genetic algorithm in a population of schedules
);

CREATE TABLE IF NOT EXISTS schedule (
	id integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
	satellite_id integer,
	ground_station_id integer,
	asset_type integer,
	start_time timestamp with time zone,
	end_time timestamp with time zone,
	status text,
	CONSTRAINT fk_asset_id FOREIGN KEY (satellite_id) REFERENCES satellite (id),
	CONSTRAINT fk_ground_station_id FOREIGN KEY (ground_station_id) REFERENCES ground_station (id)
);

CREATE INDEX IF NOT EXISTS schedule_start_time_index ON schedule (start_time);
CREATE INDEX IF NOT EXISTS schedule_end_time_index ON schedule (end_time);

CREATE TYPE order_type AS ENUM ('imaging', 'maintenance', 'gs_outage', 'sat_outage');
-- abstract table. do not define constraints on this (including primary/foreign key constraints), as it won't be inherited by the children
CREATE TABLE IF NOT EXISTS task_order (
	id integer GENERATED ALWAYS AS IDENTITY,
	schedule_id integer,
	asset_id integer DEFAULT NULL, -- optional field. if null, then the order can be fulfilled by any asset
	start_time timestamptz NOT NULL, -- maybe rename to make it clear that it is not the actual start/end time of the event, but the window in which it can be scheduled
	end_time timestamptz NOT NULL CHECK (end_time >= start_time),
	duration interval NOT NULL,
	delivery_deadline timestamptz CHECK (delivery_deadline <= end_time),
	visit_count integer NOT NULL DEFAULT 1 CHECK (visit_count>=0),
	revisit_frequency interval DEFAULT '0 days', -- if revisit_frequency is 0 days, then it is a one-time order
	priority integer DEFAULT 1 NOT NULL CHECK (priority >= 0)
);

CREATE TABLE IF NOT EXISTS transmitted_order (
	id integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
	uplink_bytes integer DEFAULT 1000 NOT NULL CHECK (uplink_bytes >= 0), -- command to transmit to asset is 1KB TODO: replace with actual value in bytes
	downlink_bytes integer DEFAULT 0 NOT NULL CHECK (downlink_bytes >= 0)
) INHERITS (task_order);

CREATE TYPE image_type AS ENUM ('low_res', 'medium_res', 'high_res');
CREATE TABLE IF NOT EXISTS image_order (
    id integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    schedule_id integer REFERENCES schedule_blueprint (id),
    latitude double precision,
    longitude double precision,
    image_type image_type,
    order_type order_type DEFAULT 'imaging'::order_type NOT NULL CHECK (order_type = 'imaging')
) INHERITS (transmitted_order);

CREATE TABLE IF NOT EXISTS maintenance_order (
	id integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
	schedule_id integer REFERENCES schedule_blueprint (id),
	operations_flag boolean,
	description text,
	order_type order_type DEFAULT 'maintenance'::order_type NOT NULL CHECK (order_type = 'maintenance'),
	asset_id integer NOT NULL -- maintenance orders must be performed on a specific asset
) INHERITS (transmitted_order);

-- abstract table. do not define constraints on this (including primary/foreign key constraints), as it won't be inherited by the children
CREATE TABLE IF NOT EXISTS outage_order (
	id integer GENERATED ALWAYS AS IDENTITY,
	schedule_id integer,
	order_type order_type CHECK (order_type = 'gs_outage' OR order_type = 'sat_outage'),
	asset_id integer NOT NULL -- outage orders must be performed on a specific asset, whether satellite or groundstation
) INHERITS (task_order);

CREATE TABLE IF NOT EXISTS gs_outage_order (
	id integer PRIMARY KEY,
	schedule_id integer REFERENCES schedule_blueprint (id),
	order_type order_type DEFAULT 'gs_outage'::order_type NOT NULL CHECK (order_type = 'gs_outage'),
	asset_id integer NOT NULL REFERENCES ground_station (id)
) INHERITS (outage_order);

CREATE INDEX IF NOT EXISTS gs_outage_order_start_time_index ON gs_outage_order (start_time);
CREATE INDEX IF NOT EXISTS gs_outage_order_end_time_index ON gs_outage_order (end_time);

CREATE TABLE IF NOT EXISTS sat_outage_order (
	id integer PRIMARY KEY,
	schedule_id integer REFERENCES schedule_blueprint (id),
	order_type order_type DEFAULT 'sat_outage'::order_type NOT NULL CHECK (order_type = 'sat_outage'),
	asset_id integer NOT NULL REFERENCES satellite (id)
) INHERITS (outage_order);

CREATE INDEX IF NOT EXISTS sat_outage_order_start_time_index ON sat_outage_order (start_time);
CREATE INDEX IF NOT EXISTS sat_outage_order_end_time_index ON sat_outage_order (end_time);

CREATE TABLE IF NOT EXISTS ground_station_request (
	id integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
	schedule_id integer,
	station_id integer,
	signal_acquisition_time timestamp with time zone,
	signal_loss_time timestamp with time zone,
	CONSTRAINT fk_schedule_id FOREIGN KEY (schedule_id) REFERENCES schedule (id),
	CONSTRAINT fk_station_id FOREIGN KEY (station_id) REFERENCES ground_station (id)
);

CREATE INDEX IF NOT EXISTS ground_station_request_signal_acquisition_index ON ground_station_request (signal_acquisition_time);
CREATE INDEX IF NOT EXISTS ground_station_request_signal_loss_index ON ground_station_request (signal_loss_time);

CREATE TYPE schedule_request_state AS ENUM ('received', 'processing', 'scheduled', 'rejected');
CREATE TABLE IF NOT EXISTS schedule_request (
	id integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
	schedule_id integer NOT NULL REFERENCES schedule_blueprint (id),
	order_id integer,
	order_type order_type, -- needed because order_id is not unique across the different order types
	asset_id integer DEFAULT NULL, -- it is null in the case where we don't care what asset it is performed on
	window_start timestamptz,
	window_end timestamptz CHECK (window_end >= window_start),
	duration interval,
	delivery_deadline timestamptz CHECK (delivery_deadline >= window_end), -- can be null if there is nothing to be delivered back, e.g. it is null for maintenance requests
	uplink_bytes integer DEFAULT 0 NOT NULL CHECK (uplink_bytes >= 0), -- there are some things we don't uplink/downlink, they will just have the default value of 0 for their uplink/downlink data size
	downlink_bytes integer DEFAULT 0 NOT NULL CHECK (downlink_bytes >= 0),
	priority integer DEFAULT 1 NOT NULL CHECK (priority >= 0),
	-- autogenerated, don't worry about this
	state schedule_request_state DEFAULT 'received'::schedule_request_state NOT NULL,
	requested_at timestamptz DEFAULT current_timestamp,
	UNIQUE (order_type, order_id, window_start)
);


CREATE TYPE asset_type AS ENUM ('satellite', 'groundstation');
CREATE TYPE event_type AS ENUM ('imaging', 'maintenance', 'gs_outage', 'sat_outage', 'contact', 'eclipse');

-- ================== Abstract tables for Scheduled Events ==================
-- NOTE: Do not define constraints on these tables (including primary/foreign key constraints), as it won't be inherited by the children
CREATE TABLE IF NOT EXISTS scheduled_event (
	id integer GENERATED ALWAYS AS IDENTITY,
	schedule_id integer NOT NULL, -- this is the schedule we are in the process of constructing
	asset_id integer NOT NULL, -- this is the resource we are scheduling to.
	start_time timestamptz NOT NULL,
	duration interval,
	window_start timestamptz DEFAULT NULL CHECK (window_start <= start_time), -- this is the start of the buffer zone. it is the earliest time this event can be shifted to
	window_end timestamptz DEFAULT NULL CHECK (window_end >= start_time+duration),
	-- these fields are auto-generated always
	event_type event_type NOT NULL,
	asset_type asset_type NOT NULL
);

CREATE TABLE IF NOT EXISTS windowed_time_event (
	start_time timestamptz NOT NULL,
	duration interval NOT NULL,
	window_start timestamptz NOT NULL,
	window_end timestamptz
) INHERITS (scheduled_event);

CREATE TABLE IF NOT EXISTS fixed_time_event (
	start_time timestamptz NOT NULL,
	duration interval NOT NULL
-- 	window_start timestamptz GENERATED ALWAYS AS (start_time) STORED,
-- 	window_end timestamptz GENERATED ALWAYS AS (start_time+duration) STORED
) INHERITS (scheduled_event);
-- ================== End of Abstract tables for Scheduled Events ==================

CREATE TABLE IF NOT EXISTS scheduled_contact (
	id integer PRIMARY KEY,
	schedule_id integer REFERENCES schedule_blueprint (id),
	asset_id integer REFERENCES satellite (id),
	groundstation_id integer REFERENCES ground_station (id),
	-- the fields below are autogenerated by the database. don't worry about them.
	event_type event_type DEFAULT 'contact'::event_type NOT NULL CHECK (event_type = 'contact')
) INHERITS (fixed_time_event);

CREATE INDEX IF NOT EXISTS scheduled_contact_start_time_index ON scheduled_contact (start_time);
CREATE INDEX IF NOT EXISTS scheduled_contact_asset_index ON scheduled_contact (asset_id);

CREATE TABLE IF NOT EXISTS groundstation_outage (
	id integer PRIMARY KEY,
	schedule_id integer REFERENCES schedule_blueprint (id),
	asset_id integer REFERENCES ground_station(id),
	request_id integer NOT NULL REFERENCES schedule_request(id),
	-- the fields below are autogenerated by the database. don't worry about them.
	event_type event_type DEFAULT 'gs_outage'::event_type NOT NULL CHECK (event_type = 'gs_outage'),
	asset_type asset_type DEFAULT 'groundstation'::asset_type NOT NULL CHECK (asset_type = 'groundstation')
) INHERITS (fixed_time_event);

CREATE INDEX IF NOT EXISTS groundstation_outage_start_time_index ON groundstation_outage (start_time);
CREATE INDEX IF NOT EXISTS groundstation_outage_asset_index ON groundstation_outage (asset_id);

CREATE TABLE IF NOT EXISTS satellite_outage (
	id integer PRIMARY KEY,
	schedule_id integer REFERENCES satellite (id),
	asset_id integer REFERENCES satellite (id),
	request_id integer NOT NULL REFERENCES schedule_request (id),
	-- the fields below are autogenerated by the database. don't worry about them.
	event_type event_type DEFAULT 'sat_outage'::event_type NOT NULL CHECK (event_type = 'sat_outage'),
	asset_type asset_type DEFAULT 'satellite'::asset_type NOT NULL CHECK (asset_type = 'satellite')
) INHERITS (fixed_time_event);

CREATE INDEX IF NOT EXISTS satellite_outage_start_time_index ON satellite_outage (start_time);
CREATE INDEX IF NOT EXISTS satellite_outage_asset_index ON satellite_outage (asset_id);

CREATE TABLE IF NOT EXISTS satellite_eclipse(
	id integer PRIMARY KEY,
	schedule_id integer REFERENCES schedule_blueprint (id),
	asset_id integer REFERENCES satellite (id),
	-- the fields below are autogenerated by the database. don't worry about them.
	event_type event_type DEFAULT 'eclipse'::event_type NOT NULL CHECK (event_type = 'eclipse'),
	asset_type asset_type DEFAULT 'satellite'::asset_type NOT NULL CHECK (asset_type = 'satellite')
) INHERITS (fixed_time_event);

CREATE INDEX IF NOT EXISTS satellite_eclipse_start_time_index ON satellite_eclipse (start_time);
CREATE INDEX IF NOT EXISTS satellite_eclipse_asset_index ON satellite_eclipse (asset_id);

-- abstract table. do not define constraints on this (including primary/foreign key constraints), as it won't be inherited by the children
CREATE TABLE IF NOT EXISTS transmitted_event (
	id integer PRIMARY KEY,
	schedule_id integer REFERENCES schedule_blueprint (id),
	asset_id integer REFERENCES satellite (id),
	request_id integer NOT NULL REFERENCES schedule_request(id),
	uplink_contact_id integer NOT NULL REFERENCES scheduled_contact (id),
	downlink_contact_id integer DEFAULT NULL REFERENCES scheduled_contact (id), -- it is nullable because not all events have data they have to transmit back to groundstation
	uplink_bytes integer DEFAULT 0 NOT NULL CHECK (uplink_bytes>=0),
	downlink_bytes integer DEFAULT 0 NOT NULL CHECK (downlink_bytes>=0),
	priority integer DEFAULT 1 NOT NULL CHECK (priority>=0), -- used to calculate throughput
	-- the fields below are autogenerated by the database. don't worry about them.
	asset_type asset_type DEFAULT 'satellite'::asset_type NOT NULL CHECK (asset_type = 'satellite')
) INHERITS (windowed_time_event);

CREATE INDEX IF NOT EXISTS transmitted_event_start_time_index ON transmitted_event (start_time);
CREATE INDEX IF NOT EXISTS transmitted_event_asset_index ON transmitted_event (asset_id);
CREATE INDEX IF NOT EXISTS transmitted_event_schedule_index ON transmitted_event (schedule_id);
CREATE INDEX IF NOT EXISTS transmitted_event_type_index ON transmitted_event (event_type);

CREATE TABLE IF NOT 
CREATE OR REPLACE VIEW scheduled_imaging AS
SELECT * FROM transmitted_event WHERE event_type = 'imaging'::event_type;

CREATE OR REPLACE VIEW scheduled_maintenance AS
SELECT * FROM transmitted_event WHERE event_type = 'maintenance'::event_type;

CREATE VIEW eventwise_satellite_state_change AS
	-- Three cases where the satellite's state changes. (calculate your state_delta in it's respective case, and leave it as 0)
	-- CASE 1: when we are uplinking the command (e.g. command to take image is uplinked)
	SELECT transmitted_event.schedule_id,
		transmitted_event.asset_id as satellite_id,
		contact.start_time as snapshot_time, -- state changes at point of contact (when uplink actually occurs)
		transmitted_event.uplink_bytes as storage_delta,
		0 as throughput_delta
	FROM transmitted_event, scheduled_contact as contact
	WHERE transmitted_event.schedule_id=contact.schedule_id
		AND transmitted_event.asset_id=contact.asset_id
		AND transmitted_event.uplink_contact_id=contact.id
	UNION ALL
	-- CASE 2: when the command is executed (e.g. image is taken)
	SELECT transmitted_event.schedule_id,
		transmitted_event.asset_id as satellite_id,
		transmitted_event.start_time as snapshot_time, -- state changes at point of execution (when the event is actually scheduled to happen on the satellite)
		transmitted_event.downlink_bytes - transmitted_event.uplink_bytes as storage_delta, -- the command data that was uplinked can be deleted now as the command has been executed. The result of the command now takes up space.
		transmitted_event.priority as throughput_delta
	FROM transmitted_event
	WHERE transmitted_event.downlink_contact_id IS NOT NULL
	UNION ALL
	-- CASE 3: when the result of the command is being downlinked (e.g. image is being downlinked)
	SELECT transmitted_event.schedule_id,
		transmitted_event.asset_id as satellite_id,
		contact.start_time as snapshot_time, -- state changes at point of contact (when downlink actually occurs. we arbitrarily chose downlink_start_time instead of downlink_end_time. which is better to use is debatable, i can't think of a strong enough reason as to why one way and not the other)
		(-1.0)*transmitted_event.downlink_bytes as storage_delta,
		0 as throughput_delta
	FROM transmitted_event, scheduled_contact as contact
	WHERE transmitted_event.schedule_id=contact.schedule_id
		AND transmitted_event.asset_id=contact.asset_id
		AND transmitted_event.downlink_contact_id=contact.id;

CREATE MATERIALIZED VIEW satellite_state_change AS
SELECT schedule_id, 
	satellite_id, 
	snapshot_time, 
	sum(storage_delta) as storage_delta, -- sum accounts for case where multiple events are scheduled for the same time that have effect on the load
	sum(throughput_delta) as throughput_delta
FROM eventwise_satellite_state_change
WHERE storage_delta <> 0.0 OR throughput_delta <> 0-- ignore cases where no change to the state
GROUP BY snapshot_time, schedule_id, satellite_id; -- aggregate changes to the load made at the same time into one change

CREATE INDEX IF NOT EXISTS snapshot_time_index ON satellite_state_change (snapshot_time);
CREATE INDEX IF NOT EXISTS satellite_schedule_index ON satellite_state_change (schedule_id, satellite_id);
CREATE INDEX IF NOT EXISTS schedule_index ON satellite_state_change (schedule_id); -- useful when calculating average satellite utilization for example - you want events for all satellites within the same schedule

