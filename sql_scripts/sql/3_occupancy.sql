
DROP TABLE IF EXISTS "occupancy";
CREATE TABLE "fullmoon"."occupancy" (
    "timestamp" integer NOT NULL,
    "occupancy" boolean NOT NULL,
    "label" text NOT NULL
) WITH (oids = false);

INSERT INTO "occupancy" ("timestamp", "occupancy", "label") VALUES
(1597661839,	'1',	'a'),
(1597661839,	'0',	'b'),
(1597661839,	'1',	'c'),
(1597661839,	'0',	'd');

-- 2020-08-17 11:32:53.169727+00