#########################################################################
#
# Copyright (C) 2012 OpenPlans
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
#########################################################################

import logging

from django.utils.translation import ugettext_lazy as _
from owslib.wcs import WebCoverageService
from owslib.coverage.wcsBase import ServiceException
import urllib
from geonode import GeoNodeException
from geonode.geoserver.helpers import ogc_server_settings

# added by ict4eo for SOS
from owslib.sos import SensorObservationService
from owslib.util import nspath_eval
from owslib.swe.observation.sos100 import namespaces

from re import sub

logger = logging.getLogger(__name__)

DEFAULT_EXCLUDE_FORMATS = ['PNG', 'JPEG', 'GIF', 'TIFF']


def wcs_links(
        wcs_url,
        identifier,
        bbox=None,
        crs=None,
        height=None,
        width=None,
        exclude_formats=True,
        quiet=True,
        version='1.0.0'):
    # FIXME(Ariel): This would only work for layers marked for public view,
    # what about the ones with permissions enabled?

    try:
        wcs = WebCoverageService(wcs_url, version=version)
    except ServiceException as err:
        err_msg = 'WCS server returned exception: %s' % err
        if not quiet:
            logger.warn(err_msg)
        raise GeoNodeException(err_msg)

    msg = ('Could not create WCS links for layer "%s",'
           ' it was not in the WCS catalog,'
           ' the available layers were: "%s"' % (
               identifier, wcs.contents.keys()))

    output = []
    formats = []

    if identifier not in wcs.contents:
        if not quiet:
            raise RuntimeError(msg)
        else:
            logger.warn(msg)
    else:
        coverage = wcs.contents[identifier]
        formats = coverage.supportedFormats
        for f in formats:
            if exclude_formats and f in DEFAULT_EXCLUDE_FORMATS:
                continue
            # roundabout, hacky way to accomplish getting a getCoverage url.
            # nonetheless, it's better than having to load an entire large
            # coverage just to generate a URL
            fakeUrl = wcs.getCoverage(identifier=coverage.id, format=f,
                                      bbox=bbox, crs=crs, height=20,
                                      width=20).geturl()
            url = sub(r'(height=)20(\&width=)20', r'\g<1>{0}\g<2>{1}',
                      fakeUrl).format(height, width)
            # The outputs are: (ext, name, mime, url)
            # FIXME(Ariel): Find a way to get proper ext, name and mime
            # using format as a default for all is not good enough
            output.append((f, f, f, url))
    return output


def _wfs_link(wfs_url, identifier, mime, extra_params):
    params = {
        'service': 'WFS',
        'version': '1.0.0',
        'request': 'GetFeature',
        'typename': identifier,
        'outputFormat': mime
    }
    params.update(extra_params)
    return wfs_url + urllib.urlencode(params)


def wfs_links(wfs_url, identifier):
    types = [
        ("zip", _("Zipped Shapefile"), "SHAPE-ZIP", {'format_options': 'charset:UTF-8'}),
        ("gml", _("GML 2.0"), "gml2", {}),
        ("gml", _("GML 3.1.1"), "text/xml; subtype=gml/3.1.1", {}),
        ("csv", _("CSV"), "csv", {}),
        ("excel", _("Excel"), "excel", {}),
        ("json", _("GeoJSON"), "json", {'srsName': 'EPSG:4326'})
    ]
    output = []
    for ext, name, mime, extra_params in types:
        url = _wfs_link(wfs_url, identifier, mime, extra_params)
        output.append((ext, name, mime, url))
    return output


def _wms_link(wms_url, identifier, mime, height, width, srid, bbox):
    return wms_url + urllib.urlencode({
        'service': 'WMS',
        'request': 'GetMap',
        'layers': identifier,
        'format': mime,
        'height': height,
        'width': width,
        'srs': srid,
        'bbox': bbox,
    })


def wms_links(wms_url, identifier, bbox, srid, height, width):
    types = [
        ("jpg", _("JPEG"), "image/jpeg"),
        ("pdf", _("PDF"), "application/pdf"),
        ("png", _("PNG"), "image/png"),
    ]
    output = []
    for ext, name, mime in types:
        url = _wms_link(wms_url, identifier, mime, height, width, srid, bbox)
        output.append((ext, name, mime, url))
    return output

############################# SOS DATA HANDLING ##############################


def sos_swe_data_list(response, constants=[], show_headers=True):
    """Return data values from SOS XML <swe:value> tag as a list of lists.
    
    Parameters
    ----------
    constants : list
        Fixed values appended to each nested list
    show_headers : boolean
        if True, inserts list of headers as first nested list
    """
    result = []
    headers = []
    _tree = etree.fromstring(response)
    data = _tree.findall(
        nspath_eval('om:member/om:Observation/om:result/swe:DataArray', 
        namespaces))
    for datum in data:
        encoding = datum.find(
            nspath_eval('swe:encoding/swe:TextBlock', namespaces))
        separators = (encoding.attrib['decimalSeparator'], 
                      encoding.attrib['tokenSeparator'], 
                      encoding.attrib['blockSeparator']) 

        if show_headers and not headers:  # only for first dataset
            fields = datum.findall(
                nspath_eval('swe:elementType/swe:DataRecord/swe:field', namespaces))
            for field in fields:
                headers.append(field.attrib['name'])
            if headers:
                result.append(headers)

        values = datum.find(nspath_eval('swe:values', namespaces))
        lines = values.text.split(separators[2]) # list of lines
        for line in lines:
            items = line.split(separators[1])  # list of items in single line
            if items:
                if constants:
                    items += constants
                result.append(items)
    return result


def sos_observation_xml(url, version='1.0.0', xml=None, offerings=[], 
                        responseFormat=None, observedProperties=[], 
                        eventTime=None, feature=None, allProperties=False):
    """Return the XML from a SOS GetObservation request.

    Parameters
    ----------
    url : string
        Full HTTP address of SOS
    version: string
        Version number of the SOS (e.g. 1.0.0)
    offerings : list
        selected offerings from SOS; defaults to all available
    responseFormat : string
        desire format for result data 
    observedProperties : list
        filters results for selected properties from SOS; defaults to first one
        (unless allProperties is True)
    eventTime : string
        filters results for a specified instant or period.
        Use ISO format YYYY-MM-DDTHH:mm:ss+-HH  Periods of time (start and end) 
        are separated by "/"; e.g. 2009-06-26T10:00:00+01/2009-06-26T11:00:00+01
    feature : string
        filters results for the ID of a feature_of_interest
    allProperties : boolean
        if allProperties is True, filters results for all properties (and
        ignores any items in the observedProperties)
    """
    # GetCapabilites of SOS
    _sos = SensorObservationService(url, version=version or '1.0.0', xml=xml or None) 
    # process any supplied offerings
    if offerings:
        for off in _sos.offerings:  # look for matching IDs
            _offerings = [off for off in _sos.offerings if off.id in offerings]
    else:
        _offerings = []
    # get offering IDs to be used
    offerings_objs = _offerings or  _sos.offerings
    sos_offerings = [off.id for off in offerings_objs]
    responseFormat = responseFormat or offerings_objs[0].response_formats[0]
    if not allProperties:
        observedProperties = observedProperties or [offering.observed_properties[0]]
    else:
        observedProperties = offering.observed_properties
    eventTime = eventTime

    if feature:
        return _sos.get_observation(
            offerings=sos_offerings, responseFormat=responseFormat,
            observedProperties=observedProperties, eventTime=eventTime,
            FEATUREOFINTEREST=feature)
    else:
        return _sos.get_observation(
            offerings=sos_offerings, responseFormat=responseFormat,
            observedProperties=observedProperties, eventTime=eventTime)

