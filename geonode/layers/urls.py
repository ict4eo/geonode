# -*- coding: utf-8 -*-
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

from django.conf.urls import patterns, url
from django.conf import settings
from django.views.generic import TemplateView

js_info_dict = {
    'packages': ('geonode.layers',),
}

urlpatterns = patterns(
    'geonode.layers.views',
    url(r'^$',
        TemplateView.as_view(template_name='layers/layer_list.html'),
        name='layer_browse'),
    url(r'^upload$', 'layer_upload', name='layer_upload'),
    url(r'^(?P<layername>[^/]*)$', 'layer_detail', name="layer_detail"),
    url(r'^(?P<layername>[^/]*)/metadata$', 'layer_metadata',
        name="layer_metadata"),
    url(r'^(?P<layername>[^/]*)/remove$', 'layer_remove', name="layer_remove"),
    url(r'^(?P<layername>[^/]*)/replace$', 'layer_replace',
        name="layer_replace"),
    #url(r'^api/batch_permissions/?$', 'batch_permissions',
    #    name='batch_permssions'),
    #url(r'^api/batch_delete/?$', 'batch_delete', name='batch_delete'),
    ########################### HANDLE SOS & WMS-T ############################
    # SOS layers
    # TODO url(r'^(?P<layername>[^/]*)/sos/csv/(?P<time>.+)$', 'sos_layer_csv', name='sos_layer_csv'),
    url(r'^(?P<layername>[^/]*)/sos/csv$', 'layer_sos_csv', name='layer_sos_csv'),
    url(r'^(?P<layername>[^/]*)/additional_metadata$', 'get_metadata', name='get_metadata'),
    # ncWMS layers
    url(r'^nclayers/$', 'layer_wmst', name='layer_wmst'),
    url(r'^nclayers/search/?$', 'layer_wmst_search', name='layer_wmst_search'),
    url(r'^nclayers/(?P<layerpart1>[^/]+)/(?P<layerpart2>[^/]*)/$', 'ncWms_detail', name="ncWms_detail"),
    #url(r'^nclayers/(?P<layerpart1>[^/]+)/(?P<layerpart2>[^/]*)/$', 'netcdf_download', name="netcdf_download"),
    # a new regex for layer of type sde:something clone the view to accept this layer
    # required because Geoserver WMS-T does not support cascaded WMS-T
    url(r'^nclayers/(?P<layername>[^/]*)/$', 'Wmst_detail', name="Wmst_detail")
)

# -- Deprecated url routes for Geoserver authentication -- remove after GeoNode 2.1
# -- Use /gs/acls, gs/resolve_user/, gs/download instead
if 'geonode.geoserver' in settings.INSTALLED_APPS:
    urlpatterns = patterns('geonode.geoserver.views',
                           url(r'^acls/?$',
                               'layer_acls',
                               name='layer_acls_dep'),
                           url(r'^resolve_user/?$',
                               'resolve_user',
                               name='layer_resolve_user_dep'),
                           url(r'^download$',
                               'layer_batch_download',
                               name='layer_batch_download_dep'),
                           ) + urlpatterns
