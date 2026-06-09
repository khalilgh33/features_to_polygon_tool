# -*- coding: utf-8 -*-
from qgis.core import QgsApplication
from .provider import FeatureToPolygonProvider


class FeatureToPolygonPlugin:

    def __init__(self, iface):
        self.iface = iface
        self.provider = None

    def initProcessing(self):
        self.provider = FeatureToPolygonProvider()
        QgsApplication.processingRegistry().addProvider(self.provider)

    def initGui(self):
        self.initProcessing()

    def unload(self):
        if self.provider:
            QgsApplication.processingRegistry().removeProvider(self.provider)
