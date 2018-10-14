# -*- coding: utf-8 -*-
"""
/***************************************************************************
    NextGIS WEB API
                              -------------------
        begin                : 2014-11-19
        git sha              : $Format:%H$
        copyright            : (C) 2014 by NextGIS
        email                : info@nextgis.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
from __future__ import absolute_import
from builtins import object
from .ngw_webmap import NGWWebMap
from .ngw_mapserver_style import NGWMapServerStyle
from .ngw_qgis_vector_style import NGWQGISVectorStyle
from .ngw_wms_service import NGWWmsService
from .ngw_wms_connection import NGWWmsConnection
from .ngw_wms_layer import NGWWmsLayer
from .ngw_vector_layer import NGWVectorLayer
from .ngw_raster_layer import NGWRasterLayer
from .ngw_raster_style import NGWRasterStyle
from .ngw_group_resource import NGWGroupResource
from .ngw_wfs_service import NGWWfsService
from .ngw_resource import NGWResource
from .ngw_base_map import NGWBaseMap

API_NGW_VERSION = '/api/component/pyramid/pkg_version'


class NGWResourceFactory(object):

    def __init__(self, ngw_connection):
        self.__res_types_register = {
            NGWResource.type_id: NGWResource,
            NGWWfsService.type_id: NGWWfsService,
            NGWWmsService.type_id: NGWWmsService,
            NGWGroupResource.type_id: NGWGroupResource,
            NGWVectorLayer.type_id: NGWVectorLayer,
            NGWMapServerStyle.type_id: NGWMapServerStyle,
            NGWQGISVectorStyle.type_id: NGWQGISVectorStyle,
            NGWRasterLayer.type_id: NGWRasterLayer,
            NGWWebMap.type_id: NGWWebMap,
            NGWRasterStyle.type_id: NGWRasterStyle,
            NGWWmsConnection.type_id: NGWWmsConnection,
            NGWWmsLayer.type_id: NGWWmsLayer,
            NGWBaseMap.type_id: NGWBaseMap,
        }
        self.__default_type = NGWResource.type_id
        self.__conn = ngw_connection

    @property
    def resources_types_registry(self):
        return self.__res_types_register

    @property
    def connection(self):
        return self.__conn

    def get_resource(self, resource_id):
        res_json = NGWResource.receive_resource_obj(self.__conn, resource_id)
        return self.get_resource_by_json(res_json)

    def get_resource_by_json(self, res_json):
        if res_json['resource']['cls'] in self.__res_types_register:
            resource = self.__res_types_register[res_json['resource']['cls']](self, res_json)
        else:
            resource = self.__res_types_register[self.__default_type](self, res_json)
        return resource

    def get_root_resource(self):
        return self.get_resource(0)

    def get_ngw_verson(self):
        return self.__conn.get(API_NGW_VERSION)
