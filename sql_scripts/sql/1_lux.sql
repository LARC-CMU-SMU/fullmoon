CREATE TABLE "lux" (
    "timestamp" integer NOT NULL,
    "label" text NOT NULL,
    "lux" integer NOT NULL
) WITH (oids = false);

CREATE INDEX "lux_timestamp" ON "lux" USING btree ("timestamp");

ALTER TABLE lux OWNER TO fullmoon;

