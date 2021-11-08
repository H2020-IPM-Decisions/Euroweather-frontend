# Euroweather frontend service
This service provides location based synthetic seasonal weather data for Europe. The service is based on gridded weather forecasts from Deutsche Wetterdienst which are downloaded and stored throughout the season by the [Euroweather backend service](https://github.com/H2020-IPM-Decisions/Euroweather-backend). The data for each location is interpolated from the 7*7km grid. 

When a request for a specific location is made for the first time during a season, the data from January 1st and up til the request date needs to be collected from the from the backend's rather big archive of NetCDF files. Thus, the user will not get the data immediately from the first request. These location initializations take place 2-4 times per day. After that, the data are cached in this service's database for quick/immediate access, and daily requests to the backend for updates ensure that the database stays up-to-date.

![Example temperature map showing the covered area](./map.png "Example temperature map showing the covered area")

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
### Initialize the database (tested in Ubuntu)
The files for initializing the database are found in this repo's `ddl/` folder
As user postgres, using psql or pgAdmin4:

```sql
-- Create db owner
CREATE USER europe_season_adm WITH PASSWORD '*** YOUR PASSWORD GOES HERE***';

-- Create db
-- as postgres
CREATE DATABASE europe_season 
    WITH 
    OWNER = europe_season_adm
    ENCODING = 'UTF8'
    LC_COLLATE = 'en_US.UTF-8'
    LC_CTYPE = 'en_US.UTF-8'
    TABLESPACE = pg_default
    CONNECTION LIMIT = -1;
```

Then, log in as europe_season_adm and run the rest of ddl_001.sql

### Installing the app
git clone, venv etc


## TODO TIDY UP THIS DOCUMENTATION

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