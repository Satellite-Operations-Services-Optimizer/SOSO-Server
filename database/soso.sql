CREATE TABLE "ground_station" (
	"id" INT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
	"latitude" DOUBLE PRECISION,
	"longitude" DOUBLE PRECISION,
	"height" DOUBLE PRECISION,
	"station_mask_receive" DOUBLE PRECISION,
	"station_mask_send" DOUBLE PRECISION,
	"uplink_rate" DOUBLE PRECISION,
	"downlink_rate" DOUBLE PRECISION
);

CREATE TABLE "satellite" (
	"id" INT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
	"two_line_element" JSON,
	"most_recent_latitude" DOUBLE PRECISION,
	"most_recent_longitude" DOUBLE PRECISION,
	"storage_capacity" DOUBLE PRECISION,
	"is_illuminated" BOOLEAN,
	"power_capacity" DOUBLE PRECISION,
	"field_of_view_max" DOUBLE PRECISION,
	"field_of_view_min" DOUBLE PRECISION,
	"maintenance_id" INT
);

CREATE TABLE "image_order" (
	"id" INT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
	"latitude_of_image" DOUBLE PRECISION,
	"longitude_of_image" DOUBLE PRECISION,
	"priority" INT,
	"image_resolution" INT,
	"image_height" INT,
	"image_width" INT,
	"image_start_time" TIMESTAMP,
	"image_end_time" TIMESTAMP,
	"delivery_downlink_deadline" TIMESTAMP,
	"is_revisited" BOOLEAN,
	"retake_count" INT,
	"retake_frequency_min_gap" INTERVAL,
	"retake_frequency_max_gap" INTERVAL,
	"status" INT
);

CREATE INDEX "idx_time" ON "image_order" (
	"image_start_time",
	"image_end_time"
);

CREATE TABLE "image_order_bridge" (
	"satellite_id" INT,
	"image_order_id" INT,
	PRIMARY KEY ("satellite_id", "image_order_id"),
	CONSTRAINT "fk_satellite_id" FOREIGN KEY ("satellite_id") REFERENCES "satellite" ("id") ON UPDATE CASCADE ON DELETE CASCADE,
	CONSTRAINT "fk_image_order_id" FOREIGN KEY ("image_order_id") REFERENCES "image_order" ("id") ON UPDATE CASCADE ON DELETE CASCADE
);

CREATE TABLE "satellite_maintenance_request" (
	"id" INT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
	"activity_description" VARCHAR,
	"start_time" TIMESTAMP,
	"end_time" TIMESTAMP,
	"duration" INTERVAL,
	"repetition" INTERVAL,
	"frequency_min_gap" INTERVAL,
	"frequency_max_gap" INTERVAL,
	"priority" INT,
	"status" INT,
	"payload_flag" BOOLEAN
);

CREATE INDEX "idx_time" ON "satellite_maintenance_request" (
	"image_start_time",
	"image_end_time"
);

CREATE TABLE "satellite_maintenance_request_bridge" (
	"satellite_id" INT,
	"maintenance_id" INT,
	PRIMARY KEY ("satellite_id", "maintenance_id"),
	CONSTRAINT "fk_satellite_id" FOREIGN KEY ("satellite_id") REFERENCES "satellite" ("id") ON UPDATE CASCADE ON DELETE CASCADE,
	CONSTRAINT "fk_maintenance_id" FOREIGN KEY ("maintenance_id") REFERENCES "satellite_maintenance_request" ("id") ON UPDATE CASCADE ON DELETE CASCADE
);

CREATE TABLE "satellite_outage_request" (
	"id" INT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
	"satellite_id" INT,
	"start_time" TIMESTAMP,
	"end_time" TIMESTAMP,
	"status" INT
);

CREATE INDEX "idx_time" ON "satellite_outage_request" (
	"image_start_time",
	"image_end_time"
);

CREATE TABLE "satellite_outage_request_bridge" (
	"satellite_id" INT,
	"outage_request_id" INT,
	PRIMARY KEY ("satellite_id", "outage_request_id"),
	CONSTRAINT "fk_satellite_id" FOREIGN KEY ("satellite_id") REFERENCES "satellite" ("id") ON UPDATE CASCADE ON DELETE CASCADE,
	CONSTRAINT "fk_outage_request_id" FOREIGN KEY ("outage_request_id") REFERENCES "satellite_outage_request" ("id") ON UPDATE CASCADE ON DELETE CASCADE
);

CREATE TABLE "ground_station_outage_request" (
	"id" INT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
	"ground_station_id" INT,
	"start_time" TIMESTAMP,
	"end_time" TIMESTAMP,
	"status" INT,
	CONSTRAINT "fk_ground_station_id" FOREIGN KEY ("ground_station_id") REFERENCES "ground_station" ("id") ON UPDATE CASCADE ON DELETE CASCADE
);

CREATE INDEX "idx_time" ON "ground_station_outage_request" (
	"image_start_time",
	"image_end_time"
);


CREATE TABLE "satellite_activity_schedule" (
	"id" INT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
	"satellite_id" INT,
	"start_time" TIMESTAMP,
	"end_time" TIMESTAMP,
	"image_activity_id" INT,
	"downlink_activity_id" INT,
	"maintenance_activity_id" INT,
	"status" INT,
	CONSTRAINT "fk_satellite_id" FOREIGN KEY ("satellite_id") REFERENCES "satellite" ("id") ON UPDATE CASCADE ON DELETE CASCADE
);

CREATE TABLE "image_activity" (
	"id" INT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
	"image_resolution" INT,
	"priority" INT,
	"image_time" TIMESTAMP,
	"satellite_activity_schedule_id" INT,
	CONSTRAINT "fk_satellite_activity_schedule_id" FOREIGN KEY ("satellite_activity_schedul_id") REFERENCES "satellite_actvity_schedule" ("id") ON UPDATE CASCADE ON DELETE CASCADE
);

CREATE TABLE "maintenance_activity" (
	"id" INT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
	"description" VARCHAR,
	"priority" INT,
	"start_time" TIMESTAMP,
	"duration" INTERVAL,
	"payload_flag" BOOLEAN,
	"satellite_activity_schedule_id" INT,
	CONSTRAINT "fk_satellite_activity_schedule_id" FOREIGN KEY ("satellite_activity_schedul_id") REFERENCES "satellite_actvity_schedule" ("id") ON UPDATE CASCADE ON DELETE CASCADE

);

CREATE TABLE "downlink_activity" (
	"id" INT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
	"image_ids" INT[],
	"start_time" TIMESTAMP,
	"stop_time" TIMESTAMP,
	"data_size" DOUBLE PRECISION,
	"satellite_activity_schedule_id" INT,
	CONSTRAINT "fk_satellite_activity_schedule_id" FOREIGN KEY ("satellite_activity_schedul_id") REFERENCES "satellite_actvity_schedule" ("id") ON UPDATE CASCADE ON DELETE CASCADE
);

CREATE TABLE "ground_station_request" (
	"id" INT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
	"station_id" INT,
	"signal_acquisition" TIMESTAMP,
	"signal_loss" TIMESTAMP,
	"satellite_activity_schedule_id" INT,
	"status" INT,
	CONSTRAINT "fk_station_id" FOREIGN KEY ("station_id") REFERENCES "ground_station" ("id") ON UPDATE CASCADE ON DELETE CASCADE,
	CONSTRAINT "fk_satellite_activity_schedule_id" FOREIGN KEY ("satellite_activity_schedule_id") REFERENCES "satellite_activity_schedule" ("id") ON UPDATE CASCADE ON DELETE CASCADE
);

COMMENT ON COLUMN "image_order"."priority" IS '1 to 3 in increasing order';

COMMENT ON COLUMN "image_order"."image_resolution" IS '1=low, 2=medium, 3=high';

COMMENT ON COLUMN "image_order"."image_end_time" IS 'With time zone, precision tbd';

COMMENT ON COLUMN "image_order"."status" IS '0=pending, 1=inProgress, 2=completed';

COMMENT ON COLUMN "satellite_maintenance_request"."priority" IS '1 to 3 in increasing order';

COMMENT ON COLUMN "satellite_maintenance_request"."status" IS '0=pending, 1=in-progress, 2=completed';

COMMENT ON COLUMN "satellite_outage_request"."start_time" IS 'with timezone';

COMMENT ON COLUMN "satellite_outage_request"."end_time" IS 'with timezone';

COMMENT ON COLUMN "satellite_outage_request"."status" IS '0=pending, 1=inProgress, 2=completed';

COMMENT ON COLUMN "ground_station_outage_request"."start_time" IS 'with timezone';

COMMENT ON COLUMN "ground_station_outage_request"."end_time" IS 'with timezone';

COMMENT ON COLUMN "ground_station_outage_request"."status" IS '0=pending, 1=inProgress, 2=completed';

COMMENT ON COLUMN "satellite_activity_schedule"."downlink_activity_id" IS 'point to junction table';

COMMENT ON COLUMN "satellite_activity_schedule"."status" IS '0=pending, 1=inProgress, 2=completed';

COMMENT ON COLUMN "ground_station_request"."status" IS '0=pending, 1=inProgress, 2=completed';