# Euroweather frontend service

&copy; 2021 NIBIO

Authors: Tor-Einar Skog (NIBIO)

## License
```
 Copyright (c) 2021 NIBIO <https://www.nibio.no/> and Met Norway <https://www.met.no/>
 
 This program is free software: you can redistribute it and/or modify
 it under the terms of the GNU Affero General Public License as published by
 the Free Software Foundation, either version 3 of the License, or
 (at your option) any later version.
 
 This program is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU Affero General Public License for more details.
 
 You should have received a copy of the GNU Affero General Public License
 along with this program.  If not, see <http://www.gnu.org/licenses/>.
 
```



# Purpose of the com/ folder
The folder is a suggested folder where you place the *.req files for tickets, so that in your `app/europe-seasondata.ini` would have the setting e.g.




```
[backend]
coms_path = /opt/Europe-seasondata/webapp/coms
```

...where `/opt/Europe-seasondata/webapp/` would be the root folder of this web application

# Syncing files with backend (gatekeeper)

The communication between frontend and backend happens with the exchange of *.req files and *.res files
The front end issues req files that contain lat-lon pairs, simply like this:

```
51.109 10.961
```

The files are named `[site_id].req`

When the backend runs, it collects all these coordinates and reads through the NetCDF files and returns data by replacing the `[site_id].req` file with a `[site_id].res`  file with json data (that needs to be converted to the IPM Decisions weather data format by this application)

So we need a common folder for exchange of these files. If the frontend and backend applications are on separate servers (which is highly recommended), this is best achieved by using rsync.

From frontend to backend:

``` bash
rsync -av --dry-run --delete /opt/Europe-seasondata/webapp/coms/ /opt/Europe-seasondata/netcdf_weather_adapter_multiple/coms/
```

From backend to frontend:

``` bash
rsync -av --dry-run --delete /opt/Europe-seasondata/netcdf_weather_adapter_multiple/coms/ /opt/Europe-seasondata/webapp/coms/
```

## Setting up the system
### Software requirements
* Ubuntu Linux, tested with v 20
* Python3
* [Flask](https://flask.palletsprojects.com/en/2.0.x/)
* PostgreSQL, tested with v12
* Apache web server

#### Installing software requirements
Example using Ubuntu

``` bash
sudo apt-get install --assume-yes postgresql apache2
```

