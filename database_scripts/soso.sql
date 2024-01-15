CREATE SCHEMA IF NOT EXISTS "soso_schema";

CREATE TABLE "soso_schema"."ground_station" (
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

CREATE TABLE "soso_schema"."satellite" (
	"id" integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
	"name" text UNIQUE,
	"tle" json,
	"storage_capacity" double precision,
	"power_capacity" double precision,
	"fov_max" double precision,
	"fov_min" double precision,
	"is_illuminated" boolean,
	"under_outage" boolean
);

CREATE TABLE "soso_schema"."schedule" (
	"id" integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
	"satellite_id" integer,
	"ground_station_id" integer,
	"asset_type" integer,
	"start_time" timestamp,
	"end_time" timestamp,
	"status" text,
	CONSTRAINT "fk_asset_id" FOREIGN KEY ("satellite_id") REFERENCES "soso_schema"."satellite" ("id"),
	CONSTRAINT "fk_ground_station_id" FOREIGN KEY ("ground_station_id") REFERENCES "soso_schema"."ground_station" ("id")
);

CREATE INDEX "schedule_start_time_index" ON "soso_schema"."schedule" (
	"start_time"
);

CREATE INDEX "schedule_end_time_index" ON "soso_schema"."schedule" (
	"end_time"
);

CREATE TABLE "soso_schema"."image_order" (
	"id" integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
	"latitude" double precision,
	"longitude" double precision,
	"priority" integer,
	"image_res" integer,
	"image_height" integer,
	"image_width" integer,
	"start_time" timestamp,
	"end_time" timestamp,
	"delivery_deadline" timestamp,
	"revisit" boolean,
	"retake_count" integer,
	--"retake_freq_min" integer,
	--"retake_freq_max" integer,
	"retake_freq" integer,
	"retake_freq_units" text UNIQUE,
	"parent_id" integer,
	"child_id" integer
);

CREATE INDEX "image_order_start_time_index" ON "soso_schema"."image_order" (
	"start_time"
);

CREATE INDEX "image_order_end_time_index" ON "soso_schema"."image_order" (
	"end_time"
);

CREATE INDEX "image_order_delivery_deadline_index" ON "soso_schema"."image_order" (
	"delivery_deadline"
);

CREATE TABLE "soso_schema"."maintenance_order" (
	"id" integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
	"asset_name" text,
	"start_time" timestamp,
	"end_time" timestamp,
	"duration" time,
	"repetition" integer,
	"frequency_max" integer,
	"frequency_min" integer,
	"operations_flag" boolean,
	"description" text
);

CREATE INDEX "maintenance_order_start_time_index" ON "soso_schema"."maintenance_order" (
	"start_time"
);

CREATE INDEX "maintenance_order_end_time_index" ON "soso_schema"."maintenance_order" (
	"end_time"
);

CREATE TABLE "soso_schema"."outage_order" (
	"id" integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
	"asset_name" text,
	"start_time" timestamp,
	"end_time" timestamp
);

CREATE INDEX "outage_order_start_time_index" ON "soso_schema"."outage_order" (
	"start_time"
);

CREATE INDEX "outage_order_end_time_index" ON "soso_schema"."outage_order" (
	"end_time"
);

CREATE TABLE "soso_schema"."ground_station_request" (
	"id" integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
	"schedule_id" integer UNIQUE NOT NULL,
	"station_id" integer UNIQUE NOT NULL,
	"signal_acquisition" timestamp,
	"signal_loss" timestamp,
	CONSTRAINT "fk_schedule_id" FOREIGN KEY ("schedule_id") REFERENCES "soso_schema"."schedule" ("id"),
	CONSTRAINT "fk_station_id" FOREIGN KEY ("station_id") REFERENCES "soso_schema"."ground_station" ("id")
);

CREATE INDEX "ground_station_request_signal_acquisition_index" ON "soso_schema"."ground_station_request" (
	"signal_acquisition"
);

CREATE INDEX "ground_station_request_signal_loss_index" ON "soso_schema"."ground_station_request" (
	"signal_loss"
);

CREATE TABLE "soso_schema"."scheduled_images" (
	"schedule_id" integer UNIQUE NOT NULL,
	"image_id" integer,
	"request_id" integer,
	"downlink_start" timestamp,
	"downlink_end" timestamp,
	"data_size" double precision,
	"schedule_type" integer,
	"status" text,
	PRIMARY KEY ("schedule_id", "image_id"),
	CONSTRAINT "fk_schedule_id" FOREIGN KEY ("schedule_id") REFERENCES "soso_schema"."schedule" ("id"),
	CONSTRAINT "fk_image_id" FOREIGN KEY ("image_id") REFERENCES "soso_schema"."image_order" ("id"),
	CONSTRAINT "fk_request_id" FOREIGN KEY ("request_id") REFERENCES "soso_schema"."ground_station_request" ("id")
);

CREATE INDEX "schedule_images_start" ON "soso_schema"."scheduled_images" (
	"downlink_start"
);

CREATE INDEX "schedule_images_end" ON "soso_schema"."scheduled_images" (
	"downlink_end"
);

CREATE TABLE "soso_schema"."scheduled_maintenance" (
	"schedule_id" integer UNIQUE NOT NULL,
	"maintenance_id" integer UNIQUE NOT NULL,
	"maintenance_start" timestamp,
	"maintenance_end" timestamp,
	"repetition_number" integer,
	"description" text,
	"priority" integer,
	"status" text,
	PRIMARY KEY ("schedule_id", "maintenance_id"),
	CONSTRAINT "fk_schedule_id" FOREIGN KEY ("schedule_id") REFERENCES "soso_schema"."schedule" ("id"),
	CONSTRAINT "fk_maintenance_id" FOREIGN KEY ("maintenance_id") REFERENCES "soso_schema"."maintenance_order" ("id")
);

CREATE INDEX "schedule_maintenance_start" ON "soso_schema"."scheduled_maintenance" (
	"maintenance_start"
);

CREATE INDEX "schedule_maintenance_end" ON "soso_schema"."scheduled_maintenance" (
	"maintenance_end"
);

CREATE TABLE "soso_schema"."scheduled_outages" (
	"schedule_id" integer UNIQUE NOT NULL,
	"outage_id" integer UNIQUE NOT NULL,
	"outage_start" timestamp,
	"outage_end" timestamp,
	"status" text,
	PRIMARY KEY ("schedule_id", "outage_id"),
	CONSTRAINT "fk_schedule_id" FOREIGN KEY ("schedule_id") REFERENCES "soso_schema"."schedule" ("id"),
	CONSTRAINT "fk_outage_id" FOREIGN KEY ("outage_id") REFERENCES "soso_schema"."outage_order" ("id") 
);

CREATE INDEX "schedule_outage_start" ON "soso_schema"."scheduled_outages" (
	"outage_start"
);

CREATE INDEX "schedule_outage_end" ON "soso_schema"."scheduled_outages" (
	"outage_end"
);