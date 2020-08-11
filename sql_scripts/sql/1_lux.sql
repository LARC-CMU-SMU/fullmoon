CREATE TABLE "public"."lux" (
    "timestamp" integer NOT NULL,
    "label" text NOT NULL,
    "lux" integer NOT NULL
) WITH (oids = false);

CREATE INDEX "lux_timestamp" ON "public"."lux" USING btree ("timestamp");

