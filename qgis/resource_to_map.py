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
from qgis.PyQt.QtCore import QEventLoop, QTemporaryFile, QIODevice, QUrl, pyqtSignal, QSize, QSettings
from qgis.PyQt.QtNetwork import QNetworkRequest

from qgis.core import QgsVectorLayer, QgsMapLayerRegistry, QgsMapLayer, QgsProject, QgsRectangle
from ..core.ngw_vector_layer import NGWVectorLayer
from ..core.ngw_wfs_service import NGWWfsService


def add_resource_as_geojson(resource, return_extent=False):
    if not isinstance(resource, NGWVectorLayer):
        raise Exception('Resource type is not VectorLayer!')

    qgs_geojson_layer = QgsVectorLayer(resource.get_absolute_geojson_url(), resource.common.display_name, 'ogr')

    if not qgs_geojson_layer.isValid():
        raise Exception('Layer %s can\'t be added to the map!' % resource.common.display_name)

    qgs_geojson_layer.dataProvider().setEncoding('UTF-8')

    QgsMapLayerRegistry.instance().addMapLayer(qgs_geojson_layer)

    if return_extent:
        if qgs_geojson_layer.extent().isEmpty() and qgs_geojson_layer.type() == QgsMapLayer.VectorLayer:
            qgs_geojson_layer.updateExtents()
            return qgs_geojson_layer.extent()


def add_resource_as_geojson_with_style(ngw_layer, ngw_style, return_extent=False):
    if not isinstance(ngw_layer, NGWVectorLayer):
        raise Exception('Resource type is not VectorLayer!')

    qgs_geojson_layer = QgsVectorLayer(ngw_layer.get_absolute_geojson_url(), ngw_layer.common.display_name, 'ogr')

    if not qgs_geojson_layer.isValid():
        raise Exception('Layer %s can\'t be added to the map!' % ngw_layer.common.display_name)

    qgs_geojson_layer.dataProvider().setEncoding('UTF-8')

    ev_loop = QEventLoop()
    dwn_qml_manager = QNetworkAccessManager()
    dwn_qml_manager.finished.connect(ev_loop.quit)
    reply = dwn_qml_manager.get(QNetworkRequest(QUrl(ngw_style.download_qml_url())))
    ev_loop.exec_()

    file = QTemporaryFile()
    if file.open(QIODevice.WriteOnly):
        file.write(reply.readAll())
        file.close()
    else:
        # raise NGWError("Can not applay style to layer %s!" % ngw_layer.common.display_name)
        pass

    qgs_geojson_layer.loadNamedStyle(
        file.fileName()
    )

    QgsMapLayerRegistry.instance().addMapLayer(qgs_geojson_layer)

    if return_extent:
        if qgs_geojson_layer.extent().isEmpty() and qgs_geojson_layer.type() == QgsMapLayer.VectorLayer:
            qgs_geojson_layer.updateExtents()
            return qgs_geojson_layer.extent()


def add_resource_as_wfs_layers(wfs_resource, return_extent=False):
    if not isinstance(wfs_resource, NGWWfsService):
        raise NGWError('Resource type is not WfsService!')
    #Extent stuff
    if return_extent:
        summary_extent = QgsRectangle()
        summary_extent.setMinimal()
    #Add group
    toc_root = QgsProject.instance().layerTreeRoot()
    layers_group = toc_root.insertGroup(0, wfs_resource.common.display_name)
    #Add layers
    for wfs_layer in wfs_resource.wfs.layers:
        url = wfs_resource.get_wfs_url(wfs_layer.keyname) + '&srsname=EPSG:3857&VERSION=1.0.0&REQUEST=GetFeature'
        qgs_wfs_layer = QgsVectorLayer(url, wfs_layer.display_name, 'WFS')
        #summarize extent
        if return_extent:
            _summ_extent(summary_extent, qgs_wfs_layer)
        QgsMapLayerRegistry.instance().addMapLayer(qgs_wfs_layer, False)
        layers_group.insertLayer(0, qgs_wfs_layer)

    if return_extent:
        return summary_extent


def _summ_extent(self, summary_extent, layer):
    layer_extent = layer.extent()

    if layer_extent.isEmpty() and layer.type() == QgsMapLayer.VectorLayer:
        layer.updateExtents()
        layer_extent = layer.extent()

    if layer_extent.isNull():
        return
