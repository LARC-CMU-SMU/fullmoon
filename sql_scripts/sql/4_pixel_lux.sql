DROP TABLE IF EXISTS "pixel_lux";
CREATE TABLE "fullmoon"."pixel_lux" (
    "timestamp" integer NOT NULL,
    "cam_label" text NOT NULL,
    "patch_label" text NOT NULL,
    "lux_label" text NOT NULL,
    "lux" real NOT NULL,
    "gray_mean" real NOT NULL,
    "gray_stddev" real NOT NULL,
    "h_mean" real NOT NULL,
    "s_mean" real NOT NULL,
    "v_mean" real NOT NULL,
    "h_stddev" real NOT NULL,
    "s_stddev" real NOT NULL,
    "v_stddev" real NOT NULL
) WITH (oids = false);

CREATE INDEX "pixel_lux_timestamp" ON "fullmoon"."pixel_lux" USING btree ("timestamp");
