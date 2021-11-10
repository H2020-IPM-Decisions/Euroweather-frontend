#!/usr/bin/python3
from datetime import datetime
import numpy
import json
import os,sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models import Site, WeatherData, LocationWeatherData

interval = 3600

DEBUG = False

parameters = [
        1001, # Temperature 2m (C)
        2001, # Rainfall (mm)
        3001, # Relative humidity (%)
        4012 # Wind 10m (m/s)
    ]

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

def import_data(coms_path, site_id) -> bool:
    res_file_path = "%s/%s.res" % (coms_path, site_id)
    try:
        res_file = open(res_file_path,"r")
        ## Import data
        data_imported = WeatherData(weatherParameters=parameters)
        location_weather_data = LocationWeatherData()
        res = json.loads(res_file.read())
        ##############
        # Data for the same timestamp are provided many times, from all the runs
        # that include them. We keep the last one only. We need to structure the
        # results in order to achieve this

        # Step 1: Group data in ref buckets
        ref_buckets = {}
        for time_paramdict in res:
            ref = time_paramdict["ref"]
            ref_bucket = ref_buckets.get(ref,None)
            if ref_bucket is None:
                ref_bucket = []
                ref_buckets[ref] = ref_bucket
            ref_bucket.append(time_paramdict)
            
        # Step 2: Iterate each bucket to find first and last epoch, both total and per ref time
        ref_periods={}
        first_epoch_total = None
        last_epoch_total = None
        for ref, ref_bucket in ref_buckets.items():
            last_epoch = None
            ref_bucket.sort(key=lambda x: x["time"])
            first_epoch = ref_bucket[0]["time"]
            previous_time = None
            for time_paramdict in ref_bucket:
                if previous_time is None or time_paramdict["time"] - previous_time == 3600:
                    last_epoch = time_paramdict["time"]
                    previous_time = time_paramdict["time"]
                else:
                    break
            ref_periods[ref] = [first_epoch,last_epoch]
            first_epoch_total = first_epoch if first_epoch_total is None else min(first_epoch, first_epoch_total) 
            last_epoch_total = last_epoch if last_epoch_total is None else max(last_epoch, last_epoch_total)
        
        #data_imported.timeStart = "%sZ" % datetime.utcfromtimestamp(first_epoch_total).isoformat()
        #data_imported.timeEnd = "%sZ" % datetime.utcfromtimestamp(last_epoch_total).isoformat()
        
        data_imported.timeStart = first_epoch_total
        data_imported.timeEnd = last_epoch_total


        if DEBUG:
            print("Period: %s-%s" % (data_imported.timeStart,data_imported.timeEnd))

        #data = [None] * (1 + int((last_epoch - first_epoch) / interval))
        data = numpy.empty(shape=((1 + int((last_epoch_total - first_epoch_total) / interval)),len(parameters)),dtype='object').tolist()
        # Step 3: Loop through each bucket in ref chronological order and assign data
        # Sort the buckets by reference time first
        refs_ordered = list(ref_buckets.keys())
        refs_ordered.sort()
        very_first = True
        for ref in refs_ordered:
            #print(ref)
            ref_bucket = ref_buckets[ref]
            # Assuming that ref_bucket was sorted in step 2, we don't do it again
            first = True
            for time_paramdict in ref_bucket:
                row_index = int((time_paramdict["time"] - first_epoch_total) / interval)
                if time_paramdict["time"] > ref_periods[time_paramdict["ref"]][1]:
                    continue
                # If it's the first value in this bucket, we skip it, since
                # the first value in each model run is considered a spin up value
                # ASSUMPTION: the bucket is sorted!!
                # Exception: The VERY FIRST time_paramdict in the very first bucket (Since we have nothing to overwrite it with)
                if very_first:
                    very_first = False
                    first = False
                if first:
                    first = False
                    continue
                for idx, parameter in enumerate(parameters):
                    strval = time_paramdict.get(param_mapping[parameter], None)
                    value = float(strval) if strval is not None else None
                    
                    if value is not None and parameter < 2000: # Temp is in kelvin
                        value = value - kelvin_0c
                    # Rainfall must be shifted 1 hr back
                    #print(data)
                    try:
                        if parameter == 2001 and row_index > 0:
                            data[row_index - 1][idx] = value if value is not None else data[row_index - 1][idx]
                        else:
                            data[row_index][idx] = value
                    except IndexError as ex:
                        print(ex)
                        print("data length=%s,row_index=%s,time=%s"%(len(data),row_index,datetime.utcfromtimestamp(time_paramdict["time"]).isoformat()))
                        exit(0)
                #previous_time = time_paramdict["time"]
                #print("%sZ: %s" % (datetime.utcfromtimestamp(time_paramdict["time"]).isoformat(), time_paramdict["rr"]))
        
        
        location_weather_data.data = data
        data_imported.locationWeatherData.append(location_weather_data)
        timeStart = WeatherData.to_epoch_seconds("%s-01-01" % datetime.now().year) # ISO date e.g. 2021-10-22 (Oct 22 2021)
        timeEnd = WeatherData.to_epoch_seconds("%s-12-31" % datetime.now().year)
        data_from_db = controller.get_weather_data_by_site(site_id, timeStart, timeEnd)
        if DEBUG:
            print(data_from_db.timeStart)
            print("IMPORT DATA %s For site id %s, current timeStart = %s" %(coms_path,site_id,
                                                                            None if data_from_db.timeStart is None else "%sZ" % datetime.utcfromtimestamp(data_from_db.timeStart).isoformat()
                                                                            ))
        controller.store_weather_data_for_site(site_id, controller.merge_weather_data(data_from_db, data_imported))
        #################
        # Remove file
        os.remove(res_file_path)
        return True
    except FileNotFoundError as ex:
        print(ex)
        return False
    return False 



def create_req_file(coms_path: str, site: Site):
    with open("%s/%s.req" % (coms_path, site.site_id),"w") as req_file:
        req_file.write("%s %s" % (site.location.y, site.location.x))


    
####
#

import configparser
from controller import Controller
from glob import glob

SITE_ROOT = os.path.dirname(os.path.realpath(__file__))
config = configparser.ConfigParser()
config.read(SITE_ROOT + "/../europe-seasondata.ini")
controller = Controller(config)

coms_init_path = config["backend"]["coms_init_path"]
coms_update_path = config["backend"]["coms_update_path"]

# INIT jobs (load data from the beginning of the season)
# Check which sites needs to be INITiated with data
for site in controller.get_all_sites():
    if controller.does_site_need_data_init(site.site_id):
        # Are we already on it? If not: create req file
        req_path = "%s/%s.req" % (coms_init_path, site.site_id)
        res_path = "%s/%s.res" % (coms_init_path, site.site_id)
        if not os.path.isfile(req_path) and not os.path.isfile(res_path):
            create_req_file(coms_init_path, site)
        

# Import INIT res files
res_files = glob("%s/*.res" % coms_init_path)
for res_file in res_files:
    import_data(coms_init_path, int(os.path.basename(res_file).split(".")[0]))

# UPDATE JOBS (Load the most recent data)
# All sites need to be updated
# 1. Check for any .res files in /coms_update folder -  import that data
res_files = glob("%s/*.res" % coms_update_path)
for res_file in res_files:
    import_data(coms_update_path, int(os.path.basename(res_file).split(".")[0]))
# 2. Create .req files for all sites in the /coms_update folder
for site in controller.get_all_sites():
    create_req_file(coms_update_path, site)

