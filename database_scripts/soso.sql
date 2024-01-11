CREATE SCHEMA IF NOT EXISTS soso_schema;

SET SEARCH_PATH = soso_schema;

CREATE TABLE IF NOT EXISTS ground_station (
	id integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
	name text UNIQUE,
	latitude double precision,
	longitude double precision,
	elevation double precision,
	station_mask double precision,
	uplink_rate double precision,
	downlink_rate double precision,
	under_outage boolean
);

CREATE TABLE IF NOT EXISTS satellite (
	id integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
	name text UNIQUE,
	tle json,
	storage_capacity double precision,
	power_capacity double precision,
	fov_max double precision,
	fov_min double precision,
	is_illuminated boolean,
	under_outage boolean
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

CREATE TABLE IF NOT EXISTS image_order (
	id integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
	latitude double precision,
	longitude double precision,
	priority integer,
	image_type text,
	image_height integer,
	image_width integer,
	start_time timestamp with time zone,
	end_time timestamp with time zone,
	delivery_deadline timestamp with time zone,
	num_of_revisits integer,
	revisit_frequency integer,
	revisit_frequency_units text
);

CREATE INDEX IF NOT EXISTS image_order_start_time_index ON image_order (start_time);
CREATE INDEX IF NOT EXISTS image_order_end_time_index ON image_order (end_time);
CREATE INDEX IF NOT EXISTS image_order_delivery_deadline_index ON image_order (delivery_deadline);

CREATE TABLE IF NOT EXISTS maintenance_order (
	id integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
	asset_name text,
	start_time timestamp with time zone,
	end_time timestamp with time zone,
	duration time,
	repetition integer,
	frequency_max integer,
	frequency_min integer,
	operations_flag boolean,
	description text
);

CREATE INDEX IF NOT EXISTS maintenance_order_start_time_index ON maintenance_order (start_time);
CREATE INDEX IF NOT EXISTS maintenance_order_end_time_index ON maintenance_order (end_time);

CREATE TABLE IF NOT EXISTS outage_order (
	id integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
	asset_name text,
	start_time timestamp with time zone,
	end_time timestamp with time zone
);

CREATE INDEX IF NOT EXISTS outage_order_start_time_index ON outage_order (start_time);
CREATE INDEX IF NOT EXISTS outage_order_end_time_index ON outage_order (end_time);

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

-- EXPERIMENTATION FOR SCHEDULING ALGORITHM
CREATE TABLE IF NOT EXISTS schedule_blueprint (
	id integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
	schedule_group integer DEFAULT NULL -- this is the group of schedules that are related to each other. e.g. schedules that all belong to the second generation of a genetic algorithm in a population of schedules
);

CREATE TYPE asset_type AS ENUM ('satellite', 'groundstation');
CREATE TYPE event_type AS ENUM ('imaging', 'maintenance', 'outage', 'contact');
CREATE TYPE event_identifier AS (
	type event_type,
	key integer
);

-- inheritance allows us to easily perform complex queries on all events at once
-- most constraints (including primary key constraints) aren't passed down onto the children tho, so we handle those in the children
CREATE TABLE IF NOT EXISTS scheduled_event (
	id integer GENERATED ALWAYS AS IDENTITY,
	event_type event_type,
	event_group text UNIQUE DEFAULT NULL, -- this is the group of events that are related to each other. e.g. a repeatable imaging event. event_group_id=image_order.id in this case because they are repeats of the same order
	schedule_id integer, -- this is the schedule we are in the process of constructing
	satellite_id integer, -- this is the resource we are scheduling to.
	asset_type asset_type,
	start_time timestamptz,
	end_time timestamptz,
	buffer_start timestamptz, -- this is the start of the buffer zone. it is the earliest time this event can be shifted to
	buffer_end timestamptz
);

CREATE TABLE IF NOT EXISTS scheduled_contact (
	id integer PRIMARY KEY,
	event_type event_type DEFAULT 'contact'::event_type NOT NULL CHECK (event_type = 'contact'),
	groundstation_id integer,
	FOREIGN KEY (asset_id) REFERENCES satellite (id),
	FOREIGN KEY (groundstation_id) REFERENCES ground_station (id),
	FOREIGN KEY (schedule_id) REFERENCES schedule_blueprint (id)
) INHERITS (scheduled_event);

CREATE INDEX IF NOT EXISTS scheduled_contact_start_time_index ON scheduled_contact (start_time);
CREATE INDEX IF NOT EXISTS scheduled_contact_end_time_index ON scheduled_contact (end_time);
CREATE INDEX IF NOT EXISTS scheduled_contact_asset_index ON scheduled_contact (asset_id);

CREATE TABLE IF NOT EXISTS groundstation_outage (
	id integer PRIMARY KEY,
	FOREIGN KEY (asset_id) REFERENCES ground_station ("id"),
	FOREIGN KEY (schedule_id) REFERENCES schedule_blueprint ("id")
) INHERITS (scheduled_event)

CREATE INDEX IF NOT EXISTS groundstation_outage_start_time_index ON groundstation_outage (start_time);
CREATE INDEX IF NOT EXISTS groundstation_outage_end_time_index ON groundstation_outage (end_time);
CREATE INDEX IF NOT EXISTS groundstation_outage_asset_index ON groundstation_outage (asset_id);



-- abstract tables for inheritance
CREATE TABLE IF NOT EXISTS satellite_event (
	asset_type asset_type DEFAULT 'satellite'::asset_type NOT NULL CHECK (asset_type = 'satellite'), -- can only uplink to satellites
	uplink_contact_id integer NOT NULL, -- all events have to be uplinked to the satellite for it to know it needs to execute it
	downlink_contact_id integer DEFAULT NULL, -- not all events have data they have to transmit back to groundstation
	uplink_data_size double precision DEFAULT 0.0 NOT NULL CHECK uplink_data_size>0.0,
	downlink_data_size double precision DEFAULT 0.0 NOT NULL CHECK uplink_data_size>0.0
) INHERITS (scheduled_event);

CREATE TABLE IF NOT EXISTS scheduled_imaging (
	id integer PRIMARY KEY,
	event_type event_type DEFAULT 'imaging'::event_type NOT NULL CHECK (event_type = 'imaging'),
	FOREIGN KEY (asset_id) REFERENCES satellite ("id"),
	FOREIGN KEY (schedule_id) REFERENCES schedule_blueprint ("id"),
	FOREIGN KEY (uplink_contact_id) REFERENCES scheduled_contact ("id"),
	FOREIGN KEY (downlink_contact_id) REFERENCES scheduled_contact ("id")
) INHERITS(satellite_event);

CREATE INDEX IF NOT EXISTS scheduled_imaging_start_time_index ON scheduled_imaging (start_time);
CREATE INDEX IF NOT EXISTS scheduled_imaging_end_time_index ON scheduled_imaging (end_time);
CREATE INDEX IF NOT EXISTS scheduled_imaging_asset_index ON scheduled_imaging (asset_id);

CREATE TABLE IF NOT EXISTS scheduled_maintenance (
	event_type event_type DEFAULT 'imaging'::event_type NOT NULL CHECK (event_type = 'imaging'),
	id integer PRIMARY KEY,
	priority integer,
	FOREIGN KEY (asset_id) REFERENCES satellite ("id"),
	FOREIGN KEY (schedule_id) REFERENCES schedule_blueprint ("id"),
	FOREIGN KEY (uplink_contact_id) REFERENCES scheduled_contact ("id"),
	CHECK (downlink_contact_id IS NULL) -- nothing to downlink
) INHERITS (satellite_event);

CREATE INDEX IF NOT EXISTS scheduled_maintenance_start_time_index ON scheduled_maintenance (start_time);
CREATE INDEX IF NOT EXISTS scheduled_maintenance_end_time_index ON scheduled_maintenance (end_time);
CREATE INDEX IF NOT EXISTS scheduled_maintenance_asset_index ON scheduled_maintenance (asset_id);

CREATE TABLE IF NOT EXISTS satellite_outage (
	event_type event_type DEFAULT 'outage'::event_type NOT NULL CHECK (event_type = 'outage'),
	id integer PRIMARY KEY,
	FOREIGN KEY (asset_id) REFERENCES satellite ("id"),
	FOREIGN KEY (schedule_id) REFERENCES schedule_blueprint ("id"),
	FOREIGN KEY (uplink_contact_id) REFERENCES scheduled_contact ("id"),
	CHECK (downlink_contact_id IS NULL) -- nothing to downlink
) INHERITS (satellite_event);

CREATE INDEX IF NOT EXISTS satellite_outage_start_time_index ON satellite_outage (start_time);
CREATE INDEX IF NOT EXISTS satellite_outage_end_time_index ON satellite_outage (end_time);
CREATE INDEX IF NOT EXISTS satellite_outage_asset_index ON satellite_outage (asset_id);


CREATE OR REPLACE MATERIALIZED VIEW satellite_state_change AS
SELECT schedule_id, 
	satellite_id, 
	snapshot_time, 
	sum(storage_delta) as storage_delta, -- sum accounts for case where multiple events are scheduled for the same time that have effect on the load
	sum(workload_delta) as workload_delta
FROM (
	-- Three cases where the satellite's state changes. (calculate your state_delta in it's respective case, and leave it as 0)
	-- CASE 1: when we are uplinking the command (e.g. command to take image is uplinked)
	SELECT satellite_event.schedule_id,
		satellite_event.asset_id as satellite_id,
		contact.start_time as snapshot_time, -- state changes at point of contact (when uplink actually occurs)
		satellite_event.uplink_data_size as storage_delta,
		0 as workload_delta
	FROM satellite_event, scheduled_contact as contact
	WHERE satellite_event.schedule_id=contact.schedule_id
		AND satellite_event.asset_id=contact.asset_id
		AND satellite_event.uplink_contact_id=contact.id
	UNION ALL
	-- CASE 2: when the command is executed (e.g. image is taken)
	SELECT sastellite_event.schedule_id,
		satellite_event.asset_id as satellite_id,
		satellite_event.start_time as snapshot_time, -- state changes at point of execution (when the event is actually scheduled to happen on the satellite)
		satellite_event.downlink_data_size - satellite_event.uplink_data_size as storage_delta, -- the command data that was uplinked can be deleted now as the command has been executed. The result of the command now takes up space.
		satellite_event.workload as workload_delta
	FROM satellite_event
	WHERE satellite_event.downlink_contact_id IS NOT NULL
	UNION ALL
	-- CASE 3: when the result of the command is being downlinked (e.g. image is being downlinked)
	SELECT satellite_event.schedule_id,
		satellite_event.asset_id as satellite_id,
		contact.start_time as snapshot_time, -- state changes at point of contact (when downlink actually occurs. we arbitrarily chose downlink_start_time instead of downlink_end_time. which is better to use is debatable, i can't think of a strong enough reason as to why one way and not the other)
		(-1)*satellite_event.downlink_data_size as storage_delta,
		0 as workload_delta
	FROM satellite_event, scheduled_contact as contact
	WHERE satellite_event.schedule_id=contact.schedule_id
		AND satellite_event.asset_id=contact.asset_id
		AND satellite_event.downlink_contact_id=contact.id
)
WHERE storage_delta <> 0.0 OR workload_delta <> 0-- ignore cases where no change to the state
GROUP BY snapshot_time -- aggregate changes to the load made at the same time into one change

CREATE UNIQUE INDEX snapshot_time_index ON satellite_state_change (snapshot_time)
CREATE UNIQUE INDEX satellite_schedule_index ON satellite_state_change (schedule_id, satellite_id)
