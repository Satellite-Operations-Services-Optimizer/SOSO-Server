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

-- CREATE TABLE IF NOT EXISTS scheduled_images (
-- 	id integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
-- 	schedule_id integer,
-- 	order_id integer,
-- 	gs_request_id integer,
-- 	start_time timestamp with time zone,
-- 	end_time timestamp with time zone,
-- 	data_size double precision,
-- 	repeat_iteration integer,
-- 	schedule_type integer,
-- 	status text,
-- 	--PRIMARY KEY("schedule_id", "order_id"),
-- 	CONSTRAINT fk_schedule_id FOREIGN KEY (schedule_id) REFERENCES schedule (id),
-- 	CONSTRAINT fk_image_order_id FOREIGN KEY (order_id) REFERENCES image_order (id),
-- 	CONSTRAINT fk_gs_request_id FOREIGN KEY (gs_request_id) REFERENCES ground_station_request (id)
-- );

-- CREATE INDEX IF NOT EXISTS schedule_images_start ON scheduled_images (start_time);
-- CREATE INDEX IF NOT EXISTS schedule_images_end ON scheduled_images (end_time);

-- CREATE TABLE IF NOT EXISTS scheduled_maintenance (
-- 	id integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
-- 	schedule_id integer,
-- 	order_id integer,
-- 	start_time timestamp with time zone,
-- 	end_time timestamp with time zone,
-- 	repetition_number integer,
-- 	description text,
-- 	priority integer,
-- 	status text,
-- 	--PRIMARY KEY("schedule_id", "maintenance_order_id"),
-- 	CONSTRAINT fk_schedule_id FOREIGN KEY (schedule_id) REFERENCES schedule (id),
-- 	CONSTRAINT fk_maintenance_order_id FOREIGN KEY (order_id) REFERENCES maintenance_order (id)
-- );

-- CREATE INDEX IF NOT EXISTS schedule_maintenance_start ON scheduled_maintenance (start_time);
-- CREATE INDEX IF NOT EXISTS schedule_maintenance_end ON scheduled_maintenance (end_time);

-- CREATE TABLE IF NOT EXISTS scheduled_outages (
-- 	id integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
-- 	schedule_id integer,
-- 	order_id integer,
-- 	start_time timestamp with time zone,
-- 	end_time timestamp with time zone,
-- 	status text,
-- 	--PRIMARY KEY ("schedule_id", "outage_order_id"),
-- 	CONSTRAINT fk_schedule_id FOREIGN KEY (schedule_id) REFERENCES schedule (id),
-- 	CONSTRAINT fk_outage_order_id FOREIGN KEY (order_id) REFERENCES outage_order (id) 
-- );

-- CREATE INDEX IF NOT EXISTS schedule_outage_start ON scheduled_outages (start_time);
-- CREATE INDEX IF NOT EXISTS schedule_outage_end ON scheduled_outages (end_time);




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

-- todo update
CREATE OR REPLACE VIEW data_transfer AS
SELECT contact.schedule_id as schedule_id,
	contact.id as contact_event_id,
	contact.asset_id as satellite_id
	contact.groundstation_id as groundstation_id
	array_agg(
		(uplinkable_event.event_type, uplinkable_event.id)::event_identifier
	) AS uplink_items,
	array_agg(
		(downlinkable_event.event_type, downlinkable_event.id)::event_identifier
	) AS downlink_items,
	sum(uplinkable_event.uplink_data_size) as uplink_data_size,
	sum(downlinkable_event.downlink_data_size) as downlink_data_size
FROM uplinkable_event, downlinkable_event, scheduled_contact as contact
WHERE uplinkable_event.asset_type = 'satellite' -- outage could be ground_station outage, so we have to specify asset_type as satellite. This is a bit hacky, TODO: figure out a better way. maybe separate tables for groundstation and satellite outage, and only satellite one is uplinkable?
	AND uplinkable_event.uplink_contact_id=contact.id
	AND downlinkable_event.downlink_contact_id=contact.id
	AND uplinkable_event.schedule_id=contact.schedule_id -- events must belong to the same schedule
	AND downlinkable_event.schedule_id=contact.schedule_id
GROUP BY contact.id


CREATE OR REPLACE VIEW satellite_load AS
SELECT scheduled_contact.schedule_id as schedule_id,
	scheduled_contact.asset_id as satellite_id, --we will also include a timestamp representing the snapshot time of the satellite load - when it changed
	scheduled_contact.start_time as snapshot_time
	LAG(snapshot_time)
	LAG(snapshot_time) OVER (PARTITION BY schedule_id, satellite_id ORDER BY snapshot_time) as previous_snapshot_time,
	--- sum... as load -- we sum up the load (all uplinks minus all downlinks) up to the snapshot time
	sum(data_transfer.uplink_data_size) - sum(data_transfer.downlink_data_size) as load
FROM data_transfer, scheduled_contact, downlinkable_event
WHERE data_transfer.contact_event_id=scheduled_contact.id
	downlinkable_event.asset_type='satellite' -- just making sure, this should always be the case
GROUP BY schedule_id, satellite_id

CREATE OR REPLACE RECURSIVE VIEW satellite_status (
	schedule_id, satellite_id, snapshot_time, storage_delta, workload_delta
) AS
-- base case (set load to 0 for the snapshot time right before the time of the first scheduled satellite event/contact - i.e. snapshot_time will be just before the event/contact with the min(start_time))
SELECT DISTINCT ON (schedule_id, satellite_id)
	schedule_id
	asset_id as satellite_id
	start_time-interval '1 microsecond' as snapshot_time -- subtracted to prevent snapshot_time overlapping with an event starting at the same time in the recursive case
	0 as storage_utilization
FROM (
	SELECT id, event_type, schedule_id, asset_id, start_time FROM satellite_event
	UNION
	SELECT id, event_type, schedule_id, asset_id, start_time FROM scheduled_contact
)
GROUP BY schedule_id, satellite_id
ORDER BY snapshot_time, 'tiebreaker_'||event_type||id -- we add a tie breaker to break ties if there are multiple events/contacts that start at the min(snapshot_time)
-- recursive cases start here
UNION
SELECT schedule_id, 
	satellite_id, 
	snapshot_time, 
	prev_storage_utilization + sum(storage_utilization_offset) as load -- sum accounts for case where multiple events are scheduled for the same time that have effect on the load
FROM (
	-- (non-recursive) calculate all the offsets to the satellite's load across time
	-- CASE 1: when we are uplinking the command (e.g. command to take image is uplinked)
	SELECT satellite_event.schedule_id,
		satellite_event.asset_id as satellite_id,
		contact.start_time as snapshot_time, -- load changes at point of contact (when uplink is actually done)
		satellite_event.uplink_data_size as load_offset
	FROM satellite_event, scheduled_contact as contact
	WHERE satellite_event.schedule_id=contact.schedule_id
		AND satellite_event.asset_id=contact.asset_id
		AND satellite_event.uplink_contact_id=contact.id
	UNION ALL
	-- CASE 2: when the command is executed (e.g. image is taken)
	SELECT sastellite_event.schedule_id,
		satellite_event.asset_id as satellite_id,
		satellite_event.start_time as snapshot_time, -- load changes at point of execution (when the event is actually scheduled to happen on the satellite)
		satellite_event.downlink_data_size as load_offset
	FROM satellite_event
	WHERE satellite_event.downlink_contact_id IS NOT NULL
	UNION ALL
	-- CASE 3: when the result of the command is being downlinked (e.g. image is being downlinked)
	SELECT schedule_id
), (
	-- (recursive) get the previous load value
)
WHERE load_offset <> 0 -- ignore cases where no change to the load
GROUP BY snapshot_time -- aggregate changes to the load made at the same time into one change
	
