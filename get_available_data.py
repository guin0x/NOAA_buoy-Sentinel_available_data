'''
By Gui Alvarenga
https://github.com/guin0x

Functions to query the Copernicus Open Access Hub (https://scihub.copernicus.eu/dhus) and check for available products.
These functions use the module buoypy by Nick Cortale to query the NDBC, available at (https://github.com/nickc1/buoypy).
-------------------------------------------------------------------------
Available functions: 
    - gad.relatime()
    - gad.historic()
    - gad_get_lat_lon_from_ndbcnoaa()
-------------------------------------------------------------------------
Difference between gad.realtime() and gad.historic():
    Historic buoy data from NDBC do not have Swell Wave Height information,
    only Standard Meteorological Data, therefore gad.historic() will look for 
    Significant Wave Height instead of Swell Wave Height. Wind Wave Height is 
    not available for historic data as well.
-------------------------------------------------------------------------
'''

import buoypy as bp
from sentinelsat import SentinelAPI, geojson_to_wkt
import geojson
import requests
import re

list_of_realtime_buoys_NOAA = [41001, 41002, 41004, 41008, 41009, 41010, 41013, 41040, 41043, 41044, 41046, 41047, 41048, 41049, 42002, 42012, 42019, 42020, 42036, 42039, 42040, 42055, 42056, 42059, 42060, 44005, 44007, 44008, 44009, 44011, 44013, 44014, 44017, 44020, 44025, 44027, 44065, 44066, 46002, 46005, 46006, 46011, 46012, 46014, 46015, 46022, 46025, 46026, 46027, 46028, 46029, 46035, 46041, 46042, 46047, 46050, 46054, 46059, 46061, 46069, 46070, 46072, 46073, 46076, 46077, 46080, 46081, 46082, 46083, 46085, 46086, 46089, 51000, 51001, 51003, 51004, 51101]

def realtime(location, username, password, swell_height, window = 24, wind_wave_height = 99, platformname='Sentinel-1', polarisationmode='VV', producttype='SLC', sensoroperationalmode='IW', auto_download='off'):
    '''
    -------------------------------------------------------------------------
    Inputs:
    - a buoy station from NDBC (http://www.ndbc.noaa.gov/)
    - username for the Copernicus Open Access Hub
    - password for the Copernicus Open Access Hub
    - minimum accepted Swell Wave Height    

    Additional Inputs and their default values, change them according to your needs.
    - window (in hours) where these boundaries are kept || default = 24
    - maximum accepted Wind Wave Height || default = 99 
    - platform name || default = 'Sentinel-1'
    - polarisation mode || default = 'VV'
    - product type || default = 'SLC'
    - sensor operational mode || default = 'IW'
    - auto download || default = 'off'
    -------------------------------------------------------------------------
    Example:

    import buoypy as bp
    from sentinelsat import SentinelAPI, geojson_to_wkt
    import geojson
    import get_available_data as gad

    gad.realtime(42055, username, password, 1, 24)

    Returns a list with all titles of available Sentinel-1 (VV, IW, SLC) products 
    for location 42055 where Swell Wave Height was above 1 mtr for a 24 h window. 
    Alternatively, one can change auto_download to 'on' to download the available 
    products. 
    -------------------------------------------------------------------------
    '''

    lat,lon = get_lat_lon_from_ndbcnoaa(location) #get lat,lon from NOAA's website
    dx = 0.001 
    #make an infinitesimal poligon around buoy as geojson
    polygon = geojson.Polygon([[(lon,lat+dx),(lon+dx,lat),(lon,lat-dx),(lon-dx,lat),(lon,lat+dx)]]) 
    api = SentinelAPI(str(username), str(password), 'https://scihub.copernicus.eu/dhus') 
    footprint = geojson_to_wkt(polygon) #convert to WKT format (for the api)
    rt = bp.realtime(location) #get realtime data available from NOAA's website    
    spec = rt.spec()
    spec = spec[spec.SwH != 99.00] #remove rows where there's no measurement

    
    swell_event, first_date, last_date, product_list = [],[],[],[]
    print('------------------')
    print('Buoy Station {}'.format(location))
    
    for i in range(len(spec['SwH'].index)):        
        if spec['SwH'][i] >= float(swell_height) and spec['WWH'][i] <=float(wind_wave_height): 
            swell_event.append(spec['SwH'].index[i])          
            if abs(swell_event[0] - swell_event[-1]).total_seconds() >= window*3600:
                first_date.append(swell_event[-1])
                last_date.append(swell_event[0])          
                swell_event = []                
                
        else: 
            swell_event = []                   
    for i in range(len(first_date)):
        print('---------------------------------------------')
        print('Swell event number {}'.format(i))
        print('{} start\n{} end'.format(first_date[i],last_date[i]))
        products = api.query(footprint, 
                            date=(first_date[i], last_date[i]), 
                            platformname = platformname, 
                            polarisationmode = polarisationmode, 
                            producttype = producttype,
                            sensoroperationalmode = sensoroperationalmode    
                            )
        if len(products)==0:
            print('No available {} {} product'.format(platformname,producttype))          

        else:         
            print("There's an available {} {} product".format(platformname,producttype)) 
            cleaning_data = str(products.keys()) 
            cleaning_data = cleaning_data[12:-2] 
            cleaning_data = cleaning_data.split(',')
            for i in range(len(cleaning_data)):
                if i == 0:
                    cleaning_data[i] = cleaning_data[i][1:-1]
                else:
                    cleaning_data[i] = cleaning_data[i][2:-1]      

            product_keys = cleaning_data

            if auto_download == 'on':
                api.download_all(products) #this line downloads the product found
            else:
                product_list.append(str(products[product_keys[i]]['title']))
            
            print('The product title is',products[product_keys[i]]['title'])

    return product_list

def historic(location, year, username, password, wave_height, window = 24, platformname='Sentinel-1', polarisationmode='VV', producttype='SLC', sensoroperationalmode='IW', auto_download='off'):
    '''
    -------------------------------------------------------------------------
    Inputs:
        - a buoy station from NDBC (http://www.ndbc.noaa.gov/)
        - minimum accepted Significant Wave Height
        - year you want to check for
        - username for the Copernicus Open Access Hub
        - password for the Copernicus Open Access Hub
        - window (in hours) where these boundaries are kept

    Additional Inputs and their default values, change them according to your needs.
        - platform name || default = 'Sentinel-1'
        - polarisation mode || default = 'VV'
        - product type || default = 'SLC'
        - sensor operational mode || default = 'IW'
        - auto download || default = 'off'
    -------------------------------------------------------------------------
    Example:

    import buoypy as bp
    from sentinelsat import SentinelAPI, geojson_to_wkt
    import geojson
    import get_available_data as gad

    gad.historic(42055, 2015, username, password, 1, 24)

    Returns a list with all titles of available Sentinel-1 (VV, IW, SLC) products 
    for location 42055, in 2015, where Significant Wave Height was above 1 mtr 
    for a 24 h window. 
    Alternatively, one can change auto_download to 'on' to download the available 
    products. 
    -------------------------------------------------------------------------
    '''

    lat,lon = get_lat_lon_from_ndbcnoaa(str(location)) #get lat,lon from NOAA's website
    dx = 0.001 
    #make an infinitesimal poligon around buoy as geojson
    polygon = geojson.Polygon([[(lon,lat+dx),(lon+dx,lat),(lon,lat-dx),(lon-dx,lat),(lon,lat+dx)]]) 
    api = SentinelAPI(str(username), str(password), 'https://scihub.copernicus.eu/dhus') 
    footprint = geojson_to_wkt(polygon) #convert to WKT format (for the api)
    ht = bp.historic_data(location,year) #get realtime data available from NOAA's website    
    data = ht.get_stand_meteo()
    data = data[data.WVHT != 99.00]
    
    swell_event, first_date, last_date, product_list = [],[],[],[]

    for i in range(len(data['WVHT'].index)):        
        if data['WVHT'][i] >= float(wave_height):            
            swell_event.append(data['WVHT'].index[i])          
            if abs(swell_event[0] - swell_event[-1]).total_seconds() >= window*3600:
                first_date.append(swell_event[0])
                last_date.append(swell_event[-1])
                swell_event = []               
                
        else:            
            swell_event = []        

    for i in range(len(first_date)):
        print('---------------------------------------------')
        print('Swell event number {}'.format(i))
        print('{} start\n{} end'.format(first_date[i],last_date[i]))
        products = api.query(footprint, 
                            date=(first_date[i], last_date[i]), 
                            platformname = platformname, 
                            polarisationmode = polarisationmode, 
                            producttype = producttype,
                            sensoroperationalmode = sensoroperationalmode    
                            )
        if len(products)==0:
            print('No available {} {} product'.format(platformname,producttype)) 
            
        else:
            print("There's an available product for swell event number {}".format(i))
            cleaning_data = str(products.keys()) 
            cleaning_data = cleaning_data[12:-2] 
            cleaning_data = cleaning_data.split(',')
            for i in range(len(cleaning_data)):
                if i == 0:
                    cleaning_data[i] = cleaning_data[i][1:-1]
                else:
                    cleaning_data[i] = cleaning_data[i][2:-1]      

            product_keys = cleaning_data
            if auto_download == 'on':
                api.download_all(products) #this line downloads the product found, you may uncomment it if you wish to automatically download it; FYI it is a very slow download
            else:
                print('The product title is',products[product_keys[i]]['title'])
                product_list.append(str(products[product_keys[i]]['title']))

    return product_list
            

def get_lat_lon_from_ndbcnoaa(index: int):
    '''
    Get latitude and longitude from the buoy station from NDBC (http://www.ndbc.noaa.gov/)
    '''
    regex_pattern = r'(\d+\.\d+) ([N|S]) (\d+\.\d+) ([W|E])'

    url = f'https://www.ndbc.noaa.gov/station_realtime.php?station={str(index)}'
    response = requests.get(url)

    if response.status_code == 200:
        html = response.text
        
        search = re.search(regex_pattern, html, re.IGNORECASE)

        if search:
            lat = float(search.group(1))
            lat_direction = search.group(2)
            lon = float(search.group(3))
            lon_direction = search.group(4)

            if lat_direction == 'S':
                lat = lat*-1.0
            if lon_direction == 'W':
                lon = lon*-1.0

            return lat, lon
        else:
            print('Regex pattern not found... ')
            return None, None
        
    else:
        print('Something went wrong while connecting to ndbc website... ' + response.status_code)
        return None, None

def any_realtime(username, password, swell_height, window = 24, wind_wave_height = 99, platformname='Sentinel-1', polarisationmode='VV', producttype='SLC', sensoroperationalmode='IW'):
    '''
    This function is useful for comparing all locations where buoy spectral data and a satellite products are available.
    After running, 'all_products[i]' represents all product titles that are available at the buoy location 'list_of_realtime_buoys_NOAA[i]'.

    If you know which location you want to investigate, use gad.realtime() instead of this one.
    -------------------------------------------------------------------------
    Inputs:
    - username for the Copernicus Open Access Hub
    - password for the Copernicus Open Access Hub
    - minimum accepted Swell Wave Height    

    Additional Inputs and their default values, change them according to your needs.
    - window (in hours) where these boundaries are kept || default = 24
    - maximum accepted Wind Wave Height || default = 99 
    - platform name || default = 'Sentinel-1'
    - polarisation mode || default = 'VV'
    - product type || default = 'SLC'
    - sensor operational mode || default = 'IW'
    -------------------------------------------------------------------------
    Example:

    import buoypy as bp
    from sentinelsat import SentinelAPI, geojson_to_wkt
    import geojson
    import get_available_data as gad

    gad.any_realtime(username, password, 1)

    Returns a tuple with all titles of available Sentinel-1 (VV, IW, SLC) products 
    for each location where Swell Wave Height was above 1 mtr for a 24 h window. 
    In the end it prints how many products are available for each location.
    -------------------------------------------------------------------------
    '''
    all_products = []
    for i in range(len(list_of_realtime_buoys_NOAA)):
        all_products += [realtime(list_of_realtime_buoys_NOAA[i], username, password, swell_height)]
    
    print('\n\n')
    print('-------------------------------------------')
    print('Below a summary with how many products per location, given at least 1 product is available')

    for i in range(len(all_products)):
        if len(all_products[i])!=0:
            print('-------------------------------------------')
            print('Buoy station {} has {} available product(s) for a {}h swell event'.format(list_of_realtime_buoys_NOAA[i],len(all_products[i]), window))

    return all_products


    






    
   



    

    

