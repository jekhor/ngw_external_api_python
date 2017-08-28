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
import sys
import json
import traceback

from PyQt4.QtCore import *

from ..core.ngw_error import NGWError
from ..core.ngw_resource import NGWResource
from ..core.ngw_resource_creator import ResourceCreator
from ..core.ngw_resource_factory import NGWResourceFactory
from ..core.ngw_webmap import NGWWebMapLayer, NGWWebMapRoot

from ..utils import log

from qt_ngw_resource_model_job_error import *


class NGWResourceModelJobResult():
    def __init__(self):
        self.added_resources = []
        self.deleted_resources = []
        self.edited_resources = []

        self.main_resource_id = -1

    def putAddedResource(self, ngw_resource, is_main=False):
        self.added_resources.append(ngw_resource)
        if is_main:
            self.main_resource_id = ngw_resource.common.id

    def putEditedResource(self, ngw_resource, is_main=False):
        self.edited_resources.append(ngw_resource)
        if is_main:
            self.main_resource_id = ngw_resource.common.id

    def putDeletedResource(self, ngw_resource):
        self.deleted_resources.append(ngw_resource)
        

class NGWResourceModelJob(QObject):
    started = pyqtSignal()
    statusChanged = pyqtSignal(unicode)
    warningOccurred = pyqtSignal(object)
    errorOccurred = pyqtSignal(object)
    dataReceived = pyqtSignal(object)
    finished = pyqtSignal()

    def __init__(self):
        QObject.__init__(self)
        self.id = self.__class__.__name__

    def generate_unique_name(self, name, present_names):
        new_name = name
        id = 1
        if new_name in present_names:
            while(new_name in present_names):
                new_name = name + "(%d)" % id
                id += 1
        return new_name

    def unique_resource_name(self, resource_name, ngw_group):
        chd_names = [ch.common.display_name for ch in ngw_group.get_children()]
        unique_resource_name = self.generate_unique_name(resource_name, chd_names)
        return unique_resource_name

    def getResourcesChain2Root(self, ngw_resource):
        ngw_resource.update()
        chain = [ngw_resource]
        parent = ngw_resource.get_parent()
        while parent is not None:
            parent.update()
            chain.insert(0, parent)
            parent = parent.get_parent()

        return chain

    def run(self):
        self.started.emit()
        try:
            self._do()

        except NGWError as e:
            log(">>> NGWError: %s %s" % (type(e), e))
            if e.type == NGWError.TypeNGWError:
                ngw_exeption_dict = json.loads(e.message)
                ngw_exeption_type = ngw_exeption_dict.get("exception")
                if ngw_exeption_type in ["HTTPForbidden", "ForbiddenError"]:
                    self.errorOccurred.emit(JobAuthorizationError(e.url))
                else:
                    self.errorOccurred.emit(
                        JobNGWError(
                            "%s" % ngw_exeption_dict.get("message", "No message"),
                             e.url
                        )
                    )

            elif e.type == NGWError.TypeRequestError:
                self.errorOccurred.emit(JobServerRequestError(self.tr("Bad http comunication.") + "%s"%e, e.url))

            elif e.type == NGWError.TypeNGWUnexpectedAnswer:
                self.errorOccurred.emit(JobNGWError(self.tr("Cann't parse server answer"), e.url))

            else:
                self.errorOccurred.emit(JobServerRequestError(self.tr("Something wrong with request to server"), e.url))                
                
        except Exception as e:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            extracted_list = traceback.extract_tb(exc_traceback)
            extracted_list = [(f.split("\\")[-1], l, func, text) for f, l, func, text in extracted_list]
            log(">>> Unexpected error: %s %s\n%s" % (type(e), e, traceback.format_list(extracted_list)) )
            self.errorOccurred.emit(JobInternalError(str(e), traceback.format_list(extracted_list)))


        self.finished.emit()

    def _do(self):
        pass


class NGWRootResourcesLoader(NGWResourceModelJob):
    def __init__(self, ngw_connection_settings, ngw_connection_class):
        log("NGWRootResourcesLoader")
        NGWResourceModelJob.__init__(self)
        self.ngw_connection_settings = ngw_connection_settings
        self.ngw_connection_class = ngw_connection_class
    def _do(self):
        # result = []
        result = NGWResourceModelJobResult()

        rsc_factory = NGWResourceFactory(self.ngw_connection_settings, self.ngw_connection_class)
        ngw_root_resource = rsc_factory.get_root_resource()
        if ngw_root_resource is not None:
            # result.append(ngw_root_resource)
            result.putAddedResource(ngw_root_resource, is_main=True)
        self.dataReceived.emit(result)


class NGWResourceUpdater(NGWResourceModelJob):
    def __init__(self, ngw_resource):
        NGWResourceModelJob.__init__(self)
        self.ngw_resource = ngw_resource

    def _do(self):
        result = NGWResourceModelJobResult()

        # self.ngw_resource.update()
        ngw_resource_children = self.ngw_resource.get_children()
        for ngw_resource_child in ngw_resource_children:
            result.putAddedResource(ngw_resource_child)
            
        # self.dataReceived.emit((self.ngw_resource, ngw_resource_children))
        self.dataReceived.emit(result)

class NGWGroupCreater(NGWResourceModelJob):
    def __init__(self, new_group_name, ngw_resource_parent):
        NGWResourceModelJob.__init__(self)
        self.new_group_name = new_group_name
        self.ngw_resource_parent = ngw_resource_parent

    def _do(self):
        new_group_name = self.unique_resource_name(self.new_group_name, self.ngw_resource_parent)

        ngw_group_resource = ResourceCreator.create_group(
            self.ngw_resource_parent,
            new_group_name
        )

        result = NGWResourceModelJobResult()
        result.putAddedResource(ngw_group_resource, is_main=True)

        self.ngw_resource_parent.update()

        self.dataReceived.emit(result)


class NGWResourceDelete(NGWResourceModelJob):
    def __init__(self, ngw_resource):
        NGWResourceModelJob.__init__(self)
        self.ngw_resource = ngw_resource

    def _do(self):
        NGWResource.delete_resource(self.ngw_resource)

        result = NGWResourceModelJobResult()
        result.putDeletedResource(self.ngw_resource)
        self.dataReceived.emit(result)


class NGWCreateWFSForVector(NGWResourceModelJob):
    def __init__(self, ngw_vector_layer, ngw_group_resource, ret_obj_num):
        NGWResourceModelJob.__init__(self)
        self.ngw_vector_layer = ngw_vector_layer
        self.ngw_group_resource = ngw_group_resource
        self.ret_obj_num = ret_obj_num

    def _do(self):
        ngw_wfs_service_name = self.unique_resource_name(
            self.ngw_vector_layer.common.display_name + "-wfs-service",
            self.ngw_group_resource)

        ngw_wfs_resource = ResourceCreator.create_wfs_service(
            ngw_wfs_service_name,
            self.ngw_group_resource,
            [self.ngw_vector_layer],
            self.ret_obj_num
        )

        result = NGWResourceModelJobResult()
        result.putAddedResource(ngw_wfs_resource, is_main=True)

        self.dataReceived.emit(result)


class NGWCreateMapForStyle(NGWResourceModelJob):
    def __init__(self, ngw_style):
        NGWResourceModelJob.__init__(self)
        self.ngw_style = ngw_style

    def _do(self):
        ngw_layer = self.ngw_style.get_parent()
        ngw_group = ngw_layer.get_parent()

        ngw_map_name = self.unique_resource_name(
            self.ngw_style.common.display_name + "-map",
            ngw_group
        )

        ngw_webmap_root_group = NGWWebMapRoot()
        ngw_webmap_root_group.appendChild(
            NGWWebMapLayer(
                self.ngw_style.common.id,
                ngw_layer.common.display_name,
                True
            )
        )

        ngw_resource = ResourceCreator.create_webmap(
            ngw_group,
            ngw_map_name,
            [item.toDict() for item in ngw_webmap_root_group.children],
            bbox=ngw_layer.extent()
        )

        result = NGWResourceModelJobResult()
        result.putAddedResource(ngw_resource, is_main=True)

        self.dataReceived.emit(result)


class NGWRenameResource(NGWResourceModelJob):
    def __init__(self, ngw_resource, new_name):
        NGWResourceModelJob.__init__(self)
        self.ngw_resource = ngw_resource
        self.new_name = new_name

    def _do(self):
        self.ngw_resource.change_name(self.new_name)

        result = NGWResourceModelJobResult()
        result.putEditedResource(self.ngw_resource, is_main=True)

        self.dataReceived.emit(result)
