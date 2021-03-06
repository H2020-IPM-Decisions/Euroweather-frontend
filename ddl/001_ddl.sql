-- Create db owner
CREATE USER europe_season_adm WITH PASSWORD '*** YOUR PASSWORD GOES HERE***';

-- Create db
-- as postgres
CREATE DATABASE europe_season 
    WITH 
    OWNER = europe_season_adm
    TEMPLATE = template0
    ENCODING = 'UTF8'
    LC_COLLATE = 'en_US.UTF-8'
    LC_CTYPE = 'en_US.UTF-8'
    TABLESPACE = pg_default
    CONNECTION LIMIT = -1;
    
-- Add PostGIS
CREATE EXTENSION IF NOT EXISTS postgis
    SCHEMA public
    VERSION "3.0.0";

    
-- Create and populate tables
CREATE TABLE site (
	site_id serial PRIMARY KEY,
	location geometry(GeometryZ,4326)
);

ALTER TABLE IF EXISTS public.site
    OWNER to europe_season_adm;
    
CREATE TABLE parameter(
	parameter_id integer PRIMARY KEY,
	title varchar(255),
	unit varchar(255)
);

ALTER TABLE IF EXISTS public.parameter
    OWNER to europe_season_adm;
    
CREATE TABLE weather_data(
	site_id integer REFERENCES public.site(site_id),
	parameter_id integer REFERENCES public.parameter(parameter_id),
	time_measured timestamp with time zone,
	log_interval integer,
	val numeric,
	CONSTRAINT weather_data_pk PRIMARY KEY(site_id, parameter_id, time_measured, log_interval)
);

ALTER TABLE IF EXISTS public.weather_data
    OWNER to europe_season_adm;

