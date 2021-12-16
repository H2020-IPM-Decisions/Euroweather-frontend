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

import os
import configparser

from datetime import datetime, timedelta
from flask import Flask
from flask import request
from flask import render_template

from controller import Controller
from custom_errors import NoDataAvailableError
from models import WeatherData

SITE_ROOT = os.path.dirname(os.path.realpath(__file__))

app = Flask(__name__)
config = configparser.ConfigParser()
config.read(SITE_ROOT + "/europe-seasondata.ini")
controller = Controller(config)

# TODO: Change this to Jan 1st of "current year"
tpl_str = "%s-01-01" if datetime.now().year > 2021 else "%s-09-24"
data_start_time = datetime.fromisoformat(tpl_str % datetime.now().year)

available_parameters = [1001,2001,3001,4012]

@app.route("/")
def index():
    return render_template("usage.html")

@app.route("/weather_data/<site_id>", methods=['GET'])
def get_weather_data_for_site(site_id):
    data = controller.get_hourly_weather_data_by_site(site_id)
    return data.as_dict()

@app.route("/weather_data", methods=['GET'])
def get_weather_data():
    longitude = request.args.get("longitude", None) # WGS84
    latitude = request.args.get("latitude", None) # WGS84
    parameters = request.args.get("parameters", None) # Comma separated list
    interval = request.args.get("interval", 3600)
    # TODO Proper time check
    # TODO !!!! Change back to default January 1st
    timeStart = WeatherData.to_epoch_seconds(request.args.get("timeStart", (tpl_str % datetime.now().year))) # ISO date e.g. 2021-10-22 (Oct 22 2021)
    # Assume that the user wants data for that whole day, so set hour to 23
    timeEnd = WeatherData.to_epoch_seconds("%sT23:00:00" % request.args.get("timeEnd", "%s-12-31" % datetime.now().year))
    
    # Is timeStart too far in the future or in the past?
    # Test of the past
    time_start_test = datetime.fromtimestamp(timeStart)
    time_end_test = datetime.fromtimestamp(timeEnd)
    if  time_start_test < data_start_time or time_end_test < data_start_time:
        return "BAD REQUEST: timeStart (%s) is before dataseries starts (%s)" % (time_start_test.isoformat(), data_start_time.isoformat()), 403
    # Max future is the day after tomorrow
    max_future = datetime.now() + timedelta(days=2)
    if time_start_test > max_future:
        return "BAD REQUEST: timeStart (%s) is after dataseries ends (%s)" % (time_start_test.isoformat(), max_future.isoformat()), 403

    
    if longitude == None or latitude == None:
        return render_template("usage.html")
    try:
        parameters = None if parameters == None else [int(i) for i in parameters.split(",")]
    except ValueError as e:
        return "BAD REQUEST: Error in specified weather parameters: %s" % e, 403
    
    # Make sure we give a warning if the request parameters that we haven't got
    if parameters is not None:
        unavailable_parameters = []
        for p in parameters:
            if not p in available_parameters:
                unavailable_parameters.append(p)
        if len(unavailable_parameters) > 0:
            return "BAD REQUEST: Parameters %s not served by Euroweather. We provide %s" % (unavailable_parameters,available_parameters), 403
    
    try:
        data = controller.get_weather_data_by_location(longitude, latitude, parameters,timeStart,timeEnd,interval)
        if isinstance(data, WeatherData):
            return data.as_dict()
        else:
            return "This is the first time this season that weather data has been requested for this location. Please allow 2 hours of initial processing time. After this, data will be updated and immediately ready on request.", 202
    except NoDataAvailableError as e:
        return "SERVICE UNAVAILABLE: Unfortunately, there is no data available at the moment.", 503

@app.route("/weather_data/<site_id>", methods=['POST'])
def post_weather_data(site_id):
    #print(request.get_json())
    test = controller.post_weather_data(request.get_json(),site_id)
    if not isinstance(test, WeatherData) and test["status"] != 200:
        return test.get("message", "Something went wrong!"), test.get("status", 500)
    
    return test.as_dict()

