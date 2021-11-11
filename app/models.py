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

from datetime import datetime
from _datetime import date

from shapely import wkb
from shapely.geometry import Point

class WeatherData:
    def __init__(self, *args, **kwargs):
        # Get the times
        self.timeStart = WeatherData.to_epoch_seconds(kwargs.get("timeStart", None))
        self.timeEnd = WeatherData.to_epoch_seconds(kwargs.get("timeEnd", None))
        self.interval = kwargs.get("interval", 3600)
        self.weatherParameters = kwargs.get("weatherParameters", None)
        self.locationWeatherData = []
        lwd_tmp = kwargs.get("locationWeatherData", [])
        if len(lwd_tmp) > 0:
            for lwd in lwd_tmp:
                self.locationWeatherData.append(LocationWeatherData(**lwd) if not isinstance(lwd, LocationWeatherData) else lwd)
         
    @classmethod
    def to_epoch_seconds(self,some_kind_of_date):
        # Epochs and None are returned as is
        # We only try to convert strings
        try:
            # if the date is an invalid string, the ValueError is propagated
            return datetime.fromisoformat(some_kind_of_date.replace("Z","+00:00")).timestamp()
        except (TypeError, AttributeError):
            if some_kind_of_date is None or isinstance(some_kind_of_date, int):
                return some_kind_of_date
            else:
                raise TypeError("Date (timeStart or timeEnd) is neither None, int or String. Please check your input!")
        
    def set_value(self, parameter, timestamp, value):
        col = self.weatherParameters.index(parameter)
        row = int((timestamp - self.timeStart) / 3600)
        self.locationWeatherData[0].data[row][col] = value

    def as_dict(self):
        retval = vars(self)
        retval["timeStart"] = None if self.timeStart is None else "%sZ" % datetime.utcfromtimestamp(self.timeStart).isoformat()
        retval["timeEnd"] = None if self.timeEnd is None else "%sZ" % datetime.utcfromtimestamp(self.timeEnd).isoformat()
        lwds_dict = []
        for lwd in self.locationWeatherData:
            lwds_dict.append(lwd.as_dict())
        retval["locationWeatherData"] = lwds_dict
        return retval 

class LocationWeatherData:
    def __init__(self, *args, **kwargs):
        self.altitude = kwargs.get("altitude", None)
        self.longitude = kwargs.get("longitude", None)
        self.latitude = kwargs.get("latitude", None)
        self.qc = kwargs.get("qc", None)
        self.data = kwargs.get("data",[])


    def as_dict(self):
        retval = vars(self)
        # Add location weather data
        return retval 

class Site:
    def __init__(self, *args, **kwargs):
        self.site_id = kwargs.get("site_id", None)
        self.location = kwargs.get("location", None)
        if self.location is not None and not isinstance(self.location, Point):
            self.location = wkb.loads(self.location,hex=True)
            
            
            