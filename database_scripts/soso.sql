CREATE SCHEMA IF NOT EXISTS "soso_schema";

CREATE TABLE IF NOT EXISTS "soso_schema"."ground_station" (
	"id" integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
	"name" text UNIQUE,
	"latitude" double precision,
	"longitude" double precision,
	"elevation" double precision,
	"station_mask" double precision,
	"uplink_rate" double precision,
	"downlink_rate" double precision,
	"under_outage" boolean
);

CREATE TABLE IF NOT EXISTS "soso_schema"."satellite" (
	"id" integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
	"name" text UNIQUE,
	"tle" json,
	"storage_capacity" double precision,
	"power_capacity" double precision,
	"fov_max" double precision,
	"fov_min" double precision,
	"is_illuminated" boolean,
	"under_outage" boolean,
);

CREATE TABLE IF NOT EXISTS "soso_schema"."schedule" (
	"id" integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
	"satellite_id" integer,
	"ground_station_id" integer,
	"asset_type" integer,
	"start_time" timestamp with time zone,
	"end_time" timestamp with time zone,
	"status" text,
	CONSTRAINT "fk_asset_id" FOREIGN KEY ("satellite_id") REFERENCES "soso_schema"."satellite" ("id"),
	CONSTRAINT "fk_ground_station_id" FOREIGN KEY ("ground_station_id") REFERENCES "soso_schema"."ground_station" ("id")
);

CREATE INDEX IF NOT EXISTS "schedule_start_time_index" ON "soso_schema"."schedule" (
	"start_time"
);

CREATE INDEX IF NOT EXISTS "schedule_end_time_index" ON "soso_schema"."schedule" (
	"end_time"
);

CREATE TABLE IF NOT EXISTS "soso_schema"."image_order" (
	"id" integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
	"latitude" double precision,
	"longitude" double precision,
	"priority" integer,
	"image_type" text,
	"image_height" integer,
	"image_width" integer,
	"start_time" timestamp with time zone,
	"end_time" timestamp with time zone,
	"delivery_deadline" timestamp with time zone,
	"num_of_revisits" integer,
	"revisit_frequency" integer,
	"revisit_frequency_units" text
	/*"retake_count" integer,
	"retake_freq_min" integer,
	"retake_freq_max" integer*/
);

CREATE INDEX IF NOT EXISTS "image_order_start_time_index" ON "soso_schema"."image_order" (
	"start_time"
);

CREATE INDEX IF NOT EXISTS "image_order_end_time_index" ON "soso_schema"."image_order" (
	"end_time"
);

CREATE INDEX IF NOT EXISTS "image_order_delivery_deadline_index" ON "soso_schema"."image_order" (
	"delivery_deadline"
);

CREATE TABLE IF NOT EXISTS "soso_schema"."maintenance_order" (
	"id" integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
	"asset_name" text,
	"start_time" timestamp with time zone,
	"end_time" timestamp with time zone,
	"duration" time,
	"repetition" integer,
	"frequency_max" integer,
	"frequency_min" integer,
	"operations_flag" boolean,
	"description" text
);

CREATE INDEX IF NOT EXISTS "maintenance_order_start_time_index" ON "soso_schema"."maintenance_order" (
	"start_time"
);

CREATE INDEX IF NOT EXISTS "maintenance_order_end_time_index" ON "soso_schema"."maintenance_order" (
	"end_time"
);

CREATE TABLE IF NOT EXISTS "soso_schema"."outage_order" (
	"id" integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
	"asset_name" text,
	"start_time" timestamp with time zone,
	"end_time" timestamp with time zone
);

CREATE INDEX IF NOT EXISTS "outage_order_start_time_index" ON "soso_schema"."outage_order" (
	"start_time"
);

CREATE INDEX IF NOT EXISTS "outage_order_end_time_index" ON "soso_schema"."outage_order" (
	"end_time"
);

CREATE TABLE IF NOT EXISTS "soso_schema"."ground_station_request" (
	"id" integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
	"schedule_id" integer,
	"station_id" integer,
	"signal_acquisition_time" timestamp with time zone,
	"signal_loss_time" timestamp with time zone,
	CONSTRAINT "fk_schedule_id" FOREIGN KEY ("schedule_id") REFERENCES "soso_schema"."schedule" ("id"),
	CONSTRAINT "fk_station_id" FOREIGN KEY ("station_id") REFERENCES "soso_schema"."ground_station" ("id")
);

CREATE INDEX IF NOT EXISTS "ground_station_request_signal_acquisition_index" ON "soso_schema"."ground_station_request" (
	"signal_acquisition"
);

CREATE INDEX IF NOT EXISTS "ground_station_request_signal_loss_index" ON "soso_schema"."ground_station_request" (
	"signal_loss"
);

CREATE TABLE IF NOT EXISTS "soso_schema"."scheduled_images" (
	"id" integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
	"schedule_id" integer,
	"image_order_id" integer,
	"gs_request_id" integer,
	"downlink_start" timestamp with time zone,
	"downlink_end" timestamp with time zone,
	"data_size" double precision,
	"repeat_iteration" integer,
	"schedule_type" integer,
	"status" text,
	--PRIMARY KEY("schedule_id", "image_order_id"),
	CONSTRAINT "fk_schedule_id" FOREIGN KEY ("schedule_id") REFERENCES "soso_schema"."schedule" ("id"),
	CONSTRAINT "fk_image_order_id" FOREIGN KEY ("image_order_id") REFERENCES "soso_schema"."image_order" ("id"),
	CONSTRAINT "fk_gs_request_id" FOREIGN KEY ("gs_request_id") REFERENCES "soso_schema"."ground_station_request" ("id")
);

CREATE INDEX IF NOT EXISTS "schedule_images_start" ON "soso_schema"."scheduled_images" (
	"downlink_start"
);

CREATE INDEX IF NOT EXISTS "schedule_images_end" ON "soso_schema"."scheduled_images" (
	"downlink_end"
);

CREATE TABLE IF NOT EXISTS "soso_schema"."scheduled_maintenance" (
	"id" integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
	"schedule_id" integer,
	"maintenace_order_id" integer,
	"maintenance_start" timestamp with time zone,
	"maintenance_end" timestamp with time zone,
	"repetition_number" integer,
	"description" text,
	"priority" integer,
	"status" text,
	--PRIMARY KEY("schedule_id", "maintenance_order_id"),
	CONSTRAINT "fk_schedule_id" FOREIGN KEY ("schedule_id") REFERENCES "soso_schema"."schedule" ("id"),
	CONSTRAINT "fk_maintenance_order_id" FOREIGN KEY ("maintenance_order_id") REFERENCES "soso_schema"."maintenance_order" ("id")
);

CREATE INDEX IF NOT EXISTS "schedule_maintenance_start" ON "soso_schema"."scheduled_maintenance" (
	"maintenance_start"
);

CREATE INDEX IF NOT EXISTS "schedule_maintenance_end" ON "soso_schema"."scheduled_maintenance" (
	"maintenance_end"
);

CREATE TABLE IF NOT EXISTS "soso_schema"."scheduled_outages" (
	"id" integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
	"schedule_id" integer,
	"outage_order_id" integer,
	"outage_start" timestamp with time zone,
	"outage_end" timestamp with time zone,
	"status" text,
	--PRIMARY KEY ("schedule_id", "outage_order_id"),
	CONSTRAINT "fk_schedule_id" FOREIGN KEY ("schedule_id") REFERENCES "soso_schema"."schedule" ("id"),
	CONSTRAINT "fk_outage_order_id" FOREIGN KEY ("outage_order_id") REFERENCES "soso_schema"."outage_order" ("id") 
);

CREATE INDEX IF NOT EXISTS "schedule_outage_start" ON "soso_schema"."scheduled_outages" (
	"outage_start"
);

CREATE INDEX IF NOT EXISTS "schedule_outage_end" ON "soso_schema"."scheduled_outages" (
	"outage_end"
);
