CREATE TABLE "dc" (
    "timestamp" integer NOT NULL,
    "label" text NOT NULL,
    "dc" integer NOT NULL,
    "pin" integer NOT NULL
) WITH (oids = false);

CREATE INDEX "dc_timestamp" ON "dc" USING btree ("timestamp");
ALTER TABLE dc OWNER TO fullmoon;



