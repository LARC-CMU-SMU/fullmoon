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

