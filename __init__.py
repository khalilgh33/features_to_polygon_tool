# -*- coding: utf-8 -*-
"""
Feature to Polygon QGIS Plugin
Generates polygons from enclosed areas formed by polygon boundaries and lines.
"""


def classFactory(iface):
    from .plugin import FeatureToPolygonPlugin
    return FeatureToPolygonPlugin(iface)
