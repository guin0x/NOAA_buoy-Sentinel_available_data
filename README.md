## By Gui Alvarenga 
https://github.com/guin0x

Functions to query the Copernicus Open Access Hub (https://scihub.copernicus.eu/dhus) and check for available products given a certain buoy station from NDBC (http://www.ndbc.noaa.gov/).<br>
These functions use the module buoypy by Nick Cortale to query the NDBC, available at (https://github.com/nickc1/buoypy).

-------------------------------------------------------------------------

Available functions: <br>
    - relatime() <br>
    - historic() <br>
    - get_lat_lon_from_ndbcnoaa() <br>
    - any_realtime()

-------------------------------------------------------------------------

Difference between realtime() and historic(): <br>
    Historic buoy data from NDBC do not have Swell Wave Height information,
    only Standard Meteorological Data, therefore gad.historic() will look for 
    Significant Wave Height instead of Swell Wave Height. Wind Wave Height is 
    not available for historic data as well.

-------------------------------------------------------------------------