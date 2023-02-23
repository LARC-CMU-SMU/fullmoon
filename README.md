# fullmoon
interact with teapot server and,
* records lux, dc, pixel values
* derive psuedo lux from pixel values
* decide the optimal lux values
* control the dc values
* calculate the optimal dc values


## Getting started
1. install docker and docker-compose
2. clone this repository
3. run the _init.sh_ to create the _docker_mount_ dir structure
4. update the _config.py_ files in each service as necessary
5. update the _patch_coordinates_ files(within ipcam and control) if nessecary
5. run `docker-compose up --build`

## services
* ipcam - periodically calcualte psuedo lux values using the pixel values from ip camera feed (and store them in db)
* record - periodically collect and stores(in db) dc values and real lux values from rpi devices (which runs teapot servers)
* control - calculate the optimal lux -> optimal dc values and change the dc values as required
    1. infinite loop (handle_newly_occupied thread) **this is stopped for now**
        1. get the OCCUPANCY_VECTOR (Boolean) for all sections
        2. if occupancy made the transform false -> true: set that section’s corresponding light to COMFORT_VALUE (because we don’t want to keep people in dark while we incrementally increase the light)
        3. sleep for SLEEP_TIME(configurable constant)
    2. infinite loop (calculate_optimized_dc_thread)
        1. get the OCCUPANCY_VECTOR (Boolean) for all sections
        2. define the OPTIMUM_LUX vector based on occupancy [eg : occupancy vector = (True, False, False, True) -> OPTIMUM_LUX = (COMFORT_VALUE, MINIMUM_VALUE, MINIMUM_VALUE, COMFORT_VALUE)]
        3. get the ALREADY_ADDED_LUX vector (using current dc values)
	4. get the CURRENT_LUX vector (from the pixel values)
	5. calculate the CURRENT_NATURAL_LUX = CURRENT_LUX - ALREADY_ADDED_LUX
        5. calculate the DEFICIT_LUX vector (DEFICIT_LUX = OPTIMUM_LUX - CURRENT_NATURAL_LUX)
        6. calculate the optimum dc levels vector(TARGET_DC) for each section using the DEFICIT_LUX and WEIGHT_MATRIX
        7. update the TARGET_DC
        8. sleep for SLEEP_TIME(configurable constant)
    3. infinite loop (set_optimized_dc_in_device thread)
        1. read the TARGET_DC
        2. for each section 
            1. if abs(TARGET_DC - current dc) > THRESHOLD_DC: set the TARGET_DC
        3. sleep for SLEEP_TIME(configurable constant)
        
## DB Schema
```sql
create table if not exists lux
(
	timestamp integer not null,
	label text not null,
	lux real not null,
	pin text not null
);

comment on table lux is 'real lux';

alter table lux owner to fullmoon;

create index if not exists lux_timestamp
	on lux (timestamp);

create table if not exists dc
(
	timestamp integer not null,
	label text not null,
	dc integer not null,
	pin integer not null
);

comment on table dc is 'dc values';

alter table dc owner to fullmoon;

create index if not exists dc_timestamp
	on dc (timestamp);

create table if not exists occupancy
(
	timestamp integer not null,
	occupancy boolean not null,
	cubical_label text not null,
	occupant_coordinates text,
	cam_label text
);

comment on table occupancy is 'occupancy';

alter table occupancy owner to fullmoon;

create table if not exists pixel_lux
(
	timestamp integer not null,
	cam_label text not null,
	patch_label text not null,
	lux_label text not null,
	lux real not null,
	gray_mean real not null,
	h_mean real not null
);

comment on table pixel_lux is 'psuedo lux';

alter table pixel_lux owner to fullmoon;

create index if not exists pixel_lux_timestamp
	on pixel_lux (timestamp);

create table if not exists fp
(
	cam_label text,
	patch_label text,
	lux_label text,
	tuple_len integer,
	pearson_corr numeric,
	x2 numeric,
	x1 numeric,
	x0 numeric,
	h_min numeric,
	h_max numeric
);

comment on table fp is 'finger print data';

alter table fp owner to fullmoon;

create table if not exists dc_cache
(
	timestamp integer not null,
	label text not null,
	dc integer not null,
	pin integer not null,
	constraint dc_cache_pk
		unique (label, pin)
);

comment on table dc_cache is 'cache table for latest dc values';

alter table dc_cache owner to fullmoon;

create table if not exists pixel_lux_cache
(
	timestamp integer not null,
	cam_label text not null,
	patch_label text not null,
	lux_label text not null,
	lux real not null,
	h_mean real not null,
	gray_mean real,
	constraint pixel_lux_cache_pk
		unique (cam_label, patch_label, lux_label)
);

comment on table pixel_lux_cache is 'cache table for latest psuedo lux values';

alter table pixel_lux_cache owner to fullmoon;

create table if not exists occupancy_cache
(
	timestamp integer not null,
	occupancy boolean not null,
	cubical_label text not null,
	occupant_coordinates text,
	cam_label text,
	constraint occupancy_cache_pk
		unique (cam_label, cubical_label)
);

comment on table occupancy_cache is 'cache table for latest occupancy values';

alter table occupancy_cache owner to fullmoon;


```

# Notes

### Backup your databases

docker exec -t your-db-container pg_dumpall -c -U postgres > dump_`date +%d-%m-%Y"_"%H_%M_%S`.sql

### Restore your databases

cat your_dump.sql | docker exec -i your-db-container psql -U postgres

https://stackoverflow.com/a/29913462
