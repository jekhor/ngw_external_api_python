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
from os import path
from .ngw_resource import NGWResource

from ..utils import ICONS_DIR


class NGWWmsConnection(NGWResource):

    type_id = 'wmsclient_connection'
    icon_path = path.join(ICONS_DIR, 'wms_connection.svg') # TODO change icon
    type_title = 'NGW WMS Connection'

    def __init__(self, resource_factory, resource_json):
        NGWResource.__init__(self, resource_factory, resource_json)
    
    def get_connection_url(self):
        return self._json.get(self.type_id, {}).get("url")

    def layers(self):
        layers = self._json.get(self.type_id, {}).get("capcache", {}).get("layers",{})
        layer_ids = [l.get("id") for l in layers if l.get("id") is not None]
        return layer_ids

    @classmethod
    def create_in_group(cls, name, ngw_group_resource, wms_url, version="1.1.1", auth=(None, None)):
        connection = ngw_group_resource._res_factory.connection
        url = ngw_group_resource.get_api_collection_url()

        params = dict(
            resource=dict(
                cls=cls.type_id,
                display_name=name,
                parent=dict(
                    id=ngw_group_resource.common.id
                )
            )
        )

        params[cls.type_id] = dict(
            url=wms_url,
            username=auth[0],
            password=auth[1],
            version=version,
            capcache="query",
        )

        result = connection.post(url, params=params)

        ngw_resource = cls(
            ngw_group_resource._res_factory,
            NGWResource.receive_resource_obj(
                connection,
                result['id']
            )
        )

        return ngw_resource
