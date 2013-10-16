#### Created by ICT4E0-Bolelang to support download of netcdf data

import urllib
#from pydap.client import open_url

#generate url function
def _opendap_links(url):
	return url 

#create and return a dictionary of link name and url 	
def opendap_links():
    types = [
        ("full dataset"),
        ("spatial subset"),
        ("temporal subset"),
        ("spatio-temporal subset"),
    ]
    output = []
    for name in types:
        url = _opendap_links('http://ict4eo.meraka.csir.co.za/eo2h_pydap/netcdfs/trmm_global_cube.nc') # note: hardcoded for testing
        output.append((name, url))
    return output

