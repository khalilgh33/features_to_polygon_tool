# -*- coding: utf-8 -*-
import os
from qgis.core import QgsProcessingProvider
from qgis.PyQt.QtGui import QIcon
from .algorithm import FeatureToPolygonAlgorithm


class FeatureToPolygonProvider(QgsProcessingProvider):

    def loadAlgorithms(self):
        self.addAlgorithm(FeatureToPolygonAlgorithm())

    def id(self):
        return "featuretopolygon"

    def name(self):
        return "Feature To Polygon"

    def longName(self):
        return self.name()

    def icon(self):
        icon_path = os.path.join(os.path.dirname(__file__), "icons", "icon.png")
        return QIcon(icon_path) if os.path.exists(icon_path) else super().icon()
