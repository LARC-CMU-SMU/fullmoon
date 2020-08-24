DROP TABLE IF EXISTS "pixel_lux";
CREATE TABLE "fullmoon"."pixel_lux" (
    "timestamp" integer NOT NULL,
    "cam_label" text NOT NULL,
    "patch_label" text NOT NULL,
    "lux" integer NOT NULL
) WITH (oids = false);

CREATE INDEX "pixel_lux_timestamp" ON "fullmoon"."pixel_lux" USING btree ("timestamp");