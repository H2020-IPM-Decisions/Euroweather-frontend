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

from datetime import datetime
from flask import Flask
from flask import request
from flask import render_template
from flask import abort

from controller import Controller
from custom_errors import NoDataAvailableError
from models import WeatherData

SITE_ROOT = os.path.dirname(os.path.realpath(__file__))

app = Flask(__name__)
config = configparser.ConfigParser()
config.read(SITE_ROOT + "/europe-seasondata.ini")
controller = Controller(config)

@app.route("/")
def index():
    return render_template("usage.html")

@app.route("/weather_data/<site_id>", methods=['GET'])
def get_weather_data_for_site(site_id):
    data = controller.get_weather_data_by_site(site_id)
    return data.as_dict()

@app.route("/weather_data", methods=['GET'])
def get_weather_data():
    longitude = request.args.get("longitude", None) # WGS84
    latitude = request.args.get("latitude", None) # WGS84
    parameters = request.args.get("parameters", None) # Comma separated list
    # TODO Proper time check
    timeStart = WeatherData.to_epoch_seconds(request.args.get("timeStart", ("%s-01-01" % datetime.now().year))) # ISO date e.g. 2021-10-22 (Oct 22 2021)
    timeEnd = WeatherData.to_epoch_seconds(request.args.get("timeEnd", "%s-12-31" % datetime.now().year))
    
    if longitude == None or latitude == None:
        return render_template("usage.html")
    try:
        parameters = None if parameters == None else [int(i) for i in parameters.split(",")]
    except ValueError as e:
        return "BAD REQUEST: Error in specified weather parameters: %s" % e, 403
    try:
        data = controller.get_weather_data_by_location(longitude, latitude, parameters,timeStart,timeEnd)
        return data if not isinstance(data, WeatherData) else data.as_dict()
    except NoDataAvailableError as e:
        return "SERVICE UNAVAILABLE: Unfortunately, there is no data available at the moment.", 503

@app.route("/weather_data/<site_id>", methods=['POST'])
def post_weather_data(site_id):
    #print(request.get_json())
    test = controller.post_weather_data(request.get_json(),site_id)
    if not isinstance(test, WeatherData) and test["status"] != 200:
        return test.get("message", "Something went wrong!"), test.get("status", 500)
    
    return test.as_dict()

