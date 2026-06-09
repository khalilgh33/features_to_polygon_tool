# -*- coding: utf-8 -*-
"""
Feature To Polygon Algorithm

Logic:
  1. Accept multiple input layers (polygon, line, point - any mix)
  2. Extract boundaries from polygons
  3. Use lines as-is
  4. Buffer points (optional, user-defined radius)
  5. Merge + node all geometries with unary_union
  6. Polygonize enclosed areas
  7. Clip to union of all input polygon extents (optional)
  8. Output new polygon layer

References:
  - Shapely polygonize: https://shapely.readthedocs.io/en/stable/manual.html#shapely.ops.polygonize
  - QGIS Processing API: https://qgis.org/pyqgis/master/core/QgsProcessingAlgorithm.html
  - van Rossum & Drake (2009): Python Reference Manual, for general Python usage
"""

from qgis.core import (
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingParameterMultipleLayers,
    QgsProcessingParameterFeatureSink,
    QgsProcessingParameterNumber,
    QgsProcessingParameterBoolean,
    QgsProcessingException,
    QgsFeatureSink,
    QgsFeature,
    QgsGeometry,
    QgsWkbTypes,
    QgsCoordinateTransform,
    QgsProject,
    QgsFields,
    QgsField,
)
from qgis.PyQt.QtCore import QCoreApplication, QVariant

try:
    from shapely.ops import polygonize, unary_union
    from shapely.geometry import MultiPolygon, Polygon
    import shapely.wkt
    SHAPELY_OK = True
except ImportError:
    SHAPELY_OK = False


def _to_shapely(qgs_geom):
    return shapely.wkt.loads(qgs_geom.asWkt())


def _to_qgs(shp_geom):
    return QgsGeometry.fromWkt(shp_geom.wkt)


class FeatureToPolygonAlgorithm(QgsProcessingAlgorithm):

    INPUT_LAYERS  = "INPUT_LAYERS"
    POINT_BUFFER  = "POINT_BUFFER"
    CLIP_OUTPUT   = "CLIP_OUTPUT"
    OUTPUT        = "OUTPUT"

    def tr(self, s):
        return QCoreApplication.translate("FeatureToPolygon", s)

    def createInstance(self):
        return FeatureToPolygonAlgorithm()

    def name(self):
        return "featuretopolygon"

    def displayName(self):
        return self.tr("Feature To Polygon")

    def group(self):
        return self.tr("Vector Geoprocessing")

    def groupId(self):
        return "vectorgeoprocessing"

    def shortHelpString(self):
        return self.tr(
            "Generates polygons from all enclosed areas formed by combining "
            "multiple input layers (polygons, lines, and/or points).\n\n"
            "- Polygon layers: their boundaries contribute to enclosure\n"
            "- Line layers: used directly as dividing boundaries\n"
            "- Point layers: buffered by the user-defined radius\n\n"
            "All layers are reprojected to the CRS of the first layer.\n\n"
            "Requires Shapely >= 1.7 in your QGIS Python environment.\n"
            "Install: pip install shapely  (OSGeo4W Shell on Windows)"
        )

    def initAlgorithm(self, config=None):

        self.addParameter(
            QgsProcessingParameterMultipleLayers(
                self.INPUT_LAYERS,
                self.tr("Input Layers (polygon, line, point — any combination)"),
                QgsProcessing.TypeVectorAnyGeometry,
            )
        )

        param_buffer = QgsProcessingParameterNumber(
            self.POINT_BUFFER,
            self.tr("Point buffer radius (map units — only used if point layers are present)"),
            type=QgsProcessingParameterNumber.Double,
            defaultValue=10.0,
            optional=True,
            minValue=0.0,
        )
        self.addParameter(param_buffer)

        self.addParameter(
            QgsProcessingParameterBoolean(
                self.CLIP_OUTPUT,
                self.tr("Clip output to input polygon extent"),
                defaultValue=True,
            )
        )

        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT,
                self.tr("Output Polygons"),
                QgsProcessing.TypeVectorPolygon,
            )
        )

    # ------------------------------------------------------------------
    def processAlgorithm(self, parameters, context, feedback):

        # 0. Shapely check
        if not SHAPELY_OK:
            raise QgsProcessingException(
                "Shapely is not installed.\n"
                "Open OSGeo4W Shell and run:  pip install shapely"
            )

        # 1. Read parameters
        layers = self.parameterAsLayerList(parameters, self.INPUT_LAYERS, context)
        if not layers:
            raise QgsProcessingException("No input layers provided.")

        clip_output  = self.parameterAsBoolean(parameters, self.CLIP_OUTPUT, context)

        # Buffer radius: optional — returns None if not set
        point_buffer = self.parameterAsDouble(parameters, self.POINT_BUFFER, context)
        # If user left it empty / 0, treat as not set
        if point_buffer is None or point_buffer <= 0:
            point_buffer = None

        # 2. Reference CRS = CRS of first layer
        ref_crs = layers[0].crs()

        # 3. Build output sink
        fields = QgsFields()
        fields.append(QgsField("ftp_id",  QVariant.Int))
        fields.append(QgsField("area_m2", QVariant.Double))

        (sink, dest_id) = self.parameterAsSink(
            parameters, self.OUTPUT, context,
            fields, QgsWkbTypes.Polygon, ref_crs
        )
        if sink is None:
            raise QgsProcessingException("Could not create output layer.")

        # 4. Process each layer
        all_lines    = []   # Shapely geometries that form boundaries
        union_poly   = None # union of all polygon inputs for clipping
        has_points   = False
        n_layers     = len(layers)

        for layer_idx, layer in enumerate(layers):
            if feedback.isCanceled():
                return {}

            feedback.setProgressText(
                f"Processing layer {layer_idx + 1}/{n_layers}: {layer.name()}"
            )

            # Reproject if needed
            layer_crs = layer.crs()
            needs_transform = layer_crs != ref_crs
            transform = None
            if needs_transform:
                transform = QgsCoordinateTransform(
                    layer_crs, ref_crs, QgsProject.instance()
                )

            geom_type = layer.geometryType()  # 0=Point, 1=Line, 2=Polygon

            features = list(layer.getFeatures())
            n_feat = len(features)

            for i, feat in enumerate(features):
                if feedback.isCanceled():
                    return {}

                qgs_geom = feat.geometry()
                if qgs_geom is None or qgs_geom.isEmpty():
                    continue

                # Reproject to reference CRS
                if needs_transform:
                    qgs_geom.transform(transform)

                # Convert to Shapely
                try:
                    shp = _to_shapely(qgs_geom)
                    if not shp.is_valid:
                        shp = shp.buffer(0)
                    if shp.is_empty:
                        continue
                except Exception as e:
                    feedback.pushWarning(f"Skipping feature {feat.id()}: {e}")
                    continue

                # ── Polygon → extract boundary ──────────────────────────
                if geom_type == QgsWkbTypes.PolygonGeometry:
                    all_lines.append(shp.boundary)
                    union_poly = shp if union_poly is None else union_poly.union(shp)

                # ── Line → use directly ─────────────────────────────────
                elif geom_type == QgsWkbTypes.LineGeometry:
                    all_lines.append(shp)

                # ── Point → buffer (if radius set) ──────────────────────
                elif geom_type == QgsWkbTypes.PointGeometry:
                    has_points = True
                    if point_buffer is None:
                        feedback.pushWarning(
                            f"Point feature {feat.id()} in layer '{layer.name()}' skipped "
                            f"— no buffer radius set. Set a radius > 0 to include points."
                        )
                        continue
                    buffered = shp.buffer(point_buffer, resolution=16)
                    all_lines.append(buffered.boundary)

                base_progress = int(70 * layer_idx / n_layers)
                step_progress = int(70 / n_layers * i / max(n_feat, 1))
                feedback.setProgress(base_progress + step_progress)

        if not all_lines:
            raise QgsProcessingException(
                "No usable geometries found across all input layers."
            )

        if has_points and point_buffer is None:
            feedback.pushWarning(
                "Point layers were present but no buffer radius was set — "
                "all point features were skipped."
            )

        # 5. Merge and node all lines (unary_union does implicit noding)
        feedback.setProgressText("Merging and noding all boundaries...")
        feedback.setProgress(70)
        merged = unary_union(all_lines)
        feedback.setProgress(78)

        # 6. Polygonize
        feedback.setProgressText("Polygonizing enclosed areas...")
        result_polys = list(polygonize(merged))
        feedback.setProgress(85)

        if not result_polys:
            raise QgsProcessingException(
                "No enclosed areas found. Possible reasons:\n"
                "  - Lines do not fully cross polygon boundaries\n"
                "  - No closed regions are formed by the input geometries\n"
                "  - Point buffers too small to intersect other features"
            )

        # 7. Clip to polygon union (optional)
        if clip_output and union_poly is not None:
            feedback.setProgressText("Clipping to polygon extent...")
            clipped = []
            for poly in result_polys:
                if feedback.isCanceled():
                    return {}
                try:
                    inter = poly.intersection(union_poly)
                    if inter.is_empty:
                        continue
                    if inter.geom_type == "Polygon":
                        clipped.append(inter)
                    elif inter.geom_type == "MultiPolygon":
                        clipped.extend(inter.geoms)
                except Exception:
                    continue
            result_polys = clipped

        feedback.setProgress(90)

        # 8. Write output
        feedback.setProgressText("Writing output features...")
        n_out = len(result_polys)

        for i, poly in enumerate(result_polys):
            if feedback.isCanceled():
                return {}
            if not poly.is_valid:
                poly = poly.buffer(0)
            if poly.is_empty:
                continue
            feat_out = QgsFeature(fields)
            feat_out.setGeometry(_to_qgs(poly))
            feat_out.setAttributes([i + 1, round(poly.area, 4)])
            sink.addFeature(feat_out, QgsFeatureSink.FastInsert)
            feedback.setProgress(90 + int(10 * i / max(n_out, 1)))

        feedback.setProgress(100)
        feedback.pushInfo(
            f"Done. {n_out} polygon(s) generated from "
            f"{n_layers} input layer(s)."
        )

        return {self.OUTPUT: dest_id}
