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

CREATE TABLE IF NOT EXISTS scheduled_images (
	id integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
	schedule_id integer,
	order_id integer,
	gs_request_id integer,
	start_time timestamp with time zone,
	end_time timestamp with time zone,
	data_size double precision,
	repeat_iteration integer,
	schedule_type integer,
	status text,
	--PRIMARY KEY("schedule_id", "order_id"),
	CONSTRAINT fk_schedule_id FOREIGN KEY (schedule_id) REFERENCES schedule (id),
	CONSTRAINT fk_image_order_id FOREIGN KEY (order_id) REFERENCES image_order (id),
	CONSTRAINT fk_gs_request_id FOREIGN KEY (gs_request_id) REFERENCES ground_station_request (id)
);

CREATE INDEX IF NOT EXISTS schedule_images_start ON scheduled_images (start_time);
CREATE INDEX IF NOT EXISTS schedule_images_end ON scheduled_images (end_time);

CREATE TABLE IF NOT EXISTS scheduled_maintenance (
	id integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
	schedule_id integer,
	order_id integer,
	start_time timestamp with time zone,
	end_time timestamp with time zone,
	repetition_number integer,
	description text,
	priority integer,
	status text,
	--PRIMARY KEY("schedule_id", "maintenance_order_id"),
	CONSTRAINT fk_schedule_id FOREIGN KEY (schedule_id) REFERENCES schedule (id),
	CONSTRAINT fk_maintenance_order_id FOREIGN KEY (order_id) REFERENCES maintenance_order (id)
);

CREATE INDEX IF NOT EXISTS schedule_maintenance_start ON scheduled_maintenance (start_time);
CREATE INDEX IF NOT EXISTS schedule_maintenance_end ON scheduled_maintenance (end_time);

CREATE TABLE IF NOT EXISTS scheduled_outages (
	id integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
	schedule_id integer,
	order_id integer,
	start_time timestamp with time zone,
	end_time timestamp with time zone,
	status text,
	--PRIMARY KEY ("schedule_id", "outage_order_id"),
	CONSTRAINT fk_schedule_id FOREIGN KEY (schedule_id) REFERENCES schedule (id),
	CONSTRAINT fk_outage_order_id FOREIGN KEY (order_id) REFERENCES outage_order (id) 
);

CREATE INDEX IF NOT EXISTS schedule_outage_start ON scheduled_outages (start_time);
CREATE INDEX IF NOT EXISTS schedule_outage_end ON scheduled_outages (end_time);
