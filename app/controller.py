#    Copyright (C) 2021  Tor-Einar Skog,  NIBIO
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.

from models import WeatherData, LocationWeatherData, Site
from custom_errors import MergeDataError

from db_pool import DBPool
from psycopg2 import extras

from shapely import wkb
from shapely.geometry import Point, LineString
from pyproj import Geod

from datetime import datetime, timedelta
import numpy
import time
import math
import os
import sys
import json
from pickle import NONE
#from imaplib import dat

SITE_ROOT = os.path.dirname(os.path.realpath(__file__))

filename= SITE_ROOT + '/../weather_data/all.nc'
#print (filename, file =sys.stderr)
param_mapping = {
    1001: "t2m",
    1002: "t2m",
    2001: "rr",
    3001: "rh2m",
    3002: "rh2m",
    4002: "ff10m",
    4012: "ff10m"
}

kelvin_0c = 272.15

interval = 3600 # Hourly values, always
location_tolerance_m = 100

DEBUG = False

class Controller:
    def __init__(self,config):
        self.config = config
        self.db_pool = DBPool(config["database"])
        
    def post_weather_data(self, json_dict,site_id):
        weather_data = WeatherData(**json_dict)
        site = self.get_weather_data_by_site(site_id)
        if site is None:
            return {"status":404,"message":"Site not found"}
        # Found the site. Ensure it's at the same location
        if self.get_location_distance(self.get_weather_data_location(weather_data), self.get_weather_data_location(site)) > location_tolerance_m:
            return {"status":400,"message":"Weather data location is more than %s meters from the site" % location_tolerance_m}
        else:
            merged_weather_data = self.merge_weather_data(site,weather_data)
            self.store_weather_data_for_site(site_id,merged_weather_data)
            return merged_weather_data
        
    def store_weather_data_for_site(self,site_id,weather_data):
        
        insert_tpl = """
        INSERT INTO weather_data (site_id, log_interval, time_measured, parameter_id, val)
        VALUES(%s,%s,to_timestamp(%s),%s,%s);
        """
        conn = self.db_pool.get_conn()
        with conn.cursor(cursor_factory=extras.RealDictCursor) as cur:
            cur.execute("DELETE FROM weather_data WHERE site_id=%s",(site_id,))
            data = weather_data.locationWeatherData[0].data
            #print(data)
            for idy, row in enumerate(data):
                idx = 0
                for col in row:
                    cur.execute(insert_tpl,(
                        site_id,
                        3600,
                        weather_data.timeStart + (3600*idy),
                        weather_data.weatherParameters[idx],
                        col
                        )
                    )
                    idx = idx + 1
            if DEBUG:
                print("inserted DATA for site_id=%s" % site_id)
        conn.commit()
        self.db_pool.put_conn(conn)

    def merge_weather_data(self, original, new):
        # Times:
        # At least one of the sets must have valid timeStart AND timeEnd
        if (original.timeStart is None or original.timeEnd is None) and (new.timeStart is None or new.timeEnd is None):
            raise MergeDataError("None of the data sets have set their time spans.")
        
        # Determine the time span
        if original.timeStart is None or new.timeStart is None:
            time_start = original.timeStart if original.timeStart is not None else new.timeStart
        else: 
            #print("Time starts: %s, %s" % ((original.timeStart,new.timeStart)))
            time_start = min(original.timeStart,new.timeStart)
        
        #print("Time ends: %s, %s" % ((original.timeEnd,new.timeEnd)))
        if original.timeEnd is None or new.timeEnd is None:
            time_end = original.timeEnd if original.timeEnd is not None else new.timeEnd
        else: 
            time_end = max(original.timeEnd,new.timeEnd)
            
        # Parameters
        parameters = list(set(original.weatherParameters + new.weatherParameters))
        #print("parameters=%s" % parameters)
        data_length = int(((time_end - time_start) / 3600) + 1)
        #print(data_length)
        #data = [[None] * len(parameters)] * data_length
        data =  numpy.empty(shape=(data_length,len(parameters)),dtype='object').tolist()
        #print("DATA LENGTH=%s" % len(data))
        # Create the empty merged object
        merged_lwd = LocationWeatherData(
            longitude = original.locationWeatherData[0].longitude,
            latitude = original.locationWeatherData[0].latitude,
            data = data
            )
        merged_weather_data = WeatherData(
            timeStart = int(time_start),
            timeEnd = int(time_end),
            interval = 3600,
            weatherParameters = parameters,
            locationWeatherData = [merged_lwd]
            )
        
        # Fill with original data first, so that the new overwrite the old
        for current_weather_data in [original,new]:
            if current_weather_data.timeStart is not None:
                current_timestamp = current_weather_data.timeStart
                #print("data length is %s" % len(current_weather_data.locationWeatherData[0].data))
                for row in current_weather_data.locationWeatherData[0].data:
                    idx = 0
                    for param in current_weather_data.weatherParameters:
                        #TODO check that we don't overwrite an existing value with an empty one
                        #print("param=%s,timestamp=%s,idx=%s" % (param, current_timestamp,idx))
                        merged_weather_data.set_value(param, current_timestamp, row[idx])
                        idx = idx + 1
                    current_timestamp = current_timestamp + 3600
            
        return merged_weather_data

    def get_location_distance(self, loc_1, loc_2):
        geod = Geod(ellps="WGS84")
        line_string = LineString([loc_1, loc_2])
        return geod.geometry_length(line_string)
    
    def get_weather_data_location(self, weather_data):
        return Point(
            float(weather_data.locationWeatherData[0].longitude),
            float(weather_data.locationWeatherData[0].latitude)
            ) 

    def get_weather_data_by_site(self, site_id, parameters, timeStart, timeEnd):
        
        conn = self.db_pool.get_conn()
        with conn.cursor(cursor_factory=extras.RealDictCursor) as cur:
            cur.execute("SELECT * FROM site WHERE site_id=%s",(site_id,))
            site = cur.fetchone()
            if site is None:
                self.db_pool.put_conn(conn)
                return None
            sql_1_tpl = "SELECT EXTRACT(epoch FROM wd.time_measured) AS epoch_seconds, wd.* FROM weather_data wd WHERE site_id=%s"
            sql_2_tpl = "AND time_measured BETWEEN to_timestamp(%s) AND to_timestamp(%s)" 
            sql_3_tpl = "AND parameter_id IN %s"
            
            sql = [sql_1_tpl]
            sql_params = [site_id]
            if timeStart is not None and timeEnd is not None:
                sql.append(sql_2_tpl)
                sql_params.append(timeStart)
                sql_params.append(timeEnd)
            if parameters != None and len(parameters) > 0:
                sql.append(sql_3_tpl)
                sql_params.append(tuple(parameters))
            if DEBUG:
                print(sql)
                print(sql_params)
            cur.execute(" ".join(sql),tuple(sql_params))
            # Build a dict hashed with timestamps
            # Also, build parameter list
            time_start = None
            time_end = None
            params = set()
            location = wkb.loads(site["location"],hex=True)
            weather_data_list = cur.fetchall()
            # Inspect the data
            for weather_data in weather_data_list:
                time_start = weather_data["epoch_seconds"] if time_start is None else min(time_start, weather_data["epoch_seconds"])
                time_end = weather_data["epoch_seconds"] if time_end is None else max(time_end, weather_data["epoch_seconds"])
                params.add(weather_data["parameter_id"])
            params = list(params)
            # We have length and dims now!
            data = [] if len(weather_data_list) == 0 else numpy.empty(shape=(int(len(weather_data_list)/len(params)),len(params)),dtype='object').tolist()
            for weather_data in weather_data_list:
                data[int((weather_data["epoch_seconds"] - time_start)/3600)][params.index(weather_data["parameter_id"])] = None if weather_data["val"] is None else float(weather_data["val"])
            lwd = LocationWeatherData(
                longitude = location.x,
                latitude = location.y,
                data = data
                )
            weather_data = WeatherData(
                weatherParameters = params,
                interval = interval,
                timeStart = None if time_start is None else int(time_start),
                timeEnd = None if time_end is None else int(time_end),
                locationWeatherData = [lwd]
                )
            self.db_pool.put_conn(conn)
            return weather_data
        

    def get_weather_data_by_location(self, longitude, latitude, parameters, timeStart, timeEnd) -> WeatherData:
        # Check if we have a site close enough
        conn = self.db_pool.get_conn()
        with conn.cursor(cursor_factory=extras.RealDictCursor) as cur:
            cur.execute("""
            SELECT ST_Distance('SRID=4326;POINT(%(longitude)s %(latitude)s)'::geography, s.location::geography, false) AS distance_meters, 
            s.* 
            FROM site s 
            WHERE ST_DWithin(location, ST_MakePoint(%(longitude)s, %(latitude)s)::geography, 1000);
            """,
            {'longitude': float(longitude), 'latitude': float(latitude)}
            )
            # If more than one: select the closest
            
            site = None
            for a_site in cur:
                site = a_site if site is None else (a_site if a_site["distance_meters"] < site["distance_meters"] else site)
        self.db_pool.put_conn(conn)
        # If none: Create the new site
        if site is None:
            site = self.create_site(longitude, latitude)
        # Get weather data
        #print("Site id=%s" % site["site_id"])
        weather_data = self.get_weather_data_by_site(site["site_id"], parameters, timeStart, timeEnd)
        # If not updated data: Return message
        return weather_data if self.is_weather_data_up_to_date(weather_data, timeStart, timeEnd) else "DATA IS NOT AVAILABLE. Please check in later"

    def get_all_sites(self):
        conn = self.db_pool.get_conn()
        all_sites = []
        with conn.cursor(cursor_factory=extras.RealDictCursor) as cur:
            cur.execute("SELECT * FROM site")
            for res in cur.fetchall():
                all_sites.append(Site(site_id=res["site_id"],location=res["location"]))
        self.db_pool.put_conn(conn)
        return all_sites
    
    def get_site(self, site_id) -> Site:
        conn = self.db_pool.get_conn()
        with conn.cursor(cursor_factory=extras.RealDictCursor) as cur:
            cur.execute("SELECT * FROM site WHERE site_id=%s",(site_id,))
            res = cur.fetchone()
            site = None if res is None else Site(site_id=site_id,location=res["location"])
        self.db_pool.put_conn(conn)
        return site
            
    def create_site(self, longitude, latitude) -> Site:
        # Create the site in db_pool
        conn = self.db_pool.get_conn()
        with conn.cursor(cursor_factory=extras.RealDictCursor) as cur:
            cur.execute("INSERT INTO site(location) VALUES(ST_SetSRID(ST_MakePoint(%s,%s,0),4326)) RETURNING site_id",(longitude,latitude))
            site_id = cur.fetchone()["site_id"]
            cur.execute("SELECT * FROM site WHERE site_id=%s",(site_id,))
            site = cur.fetchone()
            
        conn.commit()
        self.db_pool.put_conn(conn)
        return site
    
    
    def is_weather_data_up_to_date(self, weather_data:WeatherData, timeStart:str, timeEnd:str) -> bool:
        #print(weather_data)
        if weather_data is None or len(weather_data.locationWeatherData[0].data) == 0:
            return False
        #print("%s, %s" % (weather_data.timeEnd, (datetime.now() + timedelta(hours=24)).timestamp() ))
        
        return False if weather_data.timeEnd < min((datetime.now() + timedelta(hours=24)).timestamp(), timeEnd) else True
    
    # Criteria for data init: No weather data or data up until only 24 hours ago
    # TODO: Make this more intelligent (check for holes etc)
    def does_site_need_data_init(self, site_id):
        conn = self.db_pool.get_conn()
        with conn.cursor() as cur:
            cur.execute("SELECT max(time_measured) FROM weather_data WHERE site_id=%s",(site_id,))
            max_time = cur.fetchone()[0]
        self.db_pool.put_conn(conn)
        return max_time is None or max_time.timestamp() < (datetime.now() - timedelta(hours=24)).timestamp()
    