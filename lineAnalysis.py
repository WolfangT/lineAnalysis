"""lineAnalysis.py

Script for checking intersection between lines
"""

from qgis.core import *

from .tools import filter_features, PLUGIN_NAME


# Classes


class CheckIntersections(QgsTask):
    """Task for analizing intersecsions between geometry"""

    def __init__(self, layers, prospect_layer):
        super().__init__("Analysing Intersections")
        self.layers = layers
        self.prospect_layer = prospect_layer
        self.lines = tuple(filter_features(prospect_layer.getFeatures()))
        self.total_features = self.get_total_work()
        self.current_features_done = 0
        self.results = []

    def run(self):
        self.results = []
        self.current_features_done = 0
        QgsMessageLog.logMessage(
            "-" * 50
            + f"\nSearching collisions for layer: {self.prospect_layer.name()}",
            PLUGIN_NAME,
            level=Qgis.MessageLevel.Success,
        )
        for line in self.lines:
            self.results += self.check_intersections(line)
        QgsMessageLog.logMessage(
            f">Finished!\n" + "-" * 50, PLUGIN_NAME, level=Qgis.MessageLevel.Success
        )
        return True

    def get_total_work(self):
        """Get totals of features to check"""
        i = 0
        for line in self.lines:
            for layer in self.layers:
                for feat in layer.getFeatures(line.geometry().boundingBox()):
                    i += 1
        return i

    def check_intersections(self, line):
        """Checks intersections on a feature from other layers"""
        results = []
        QgsMessageLog.logMessage(
            f"-> Analising Feature with ID: {line.id()}", PLUGIN_NAME
        )
        for layer in self.layers:
            QgsMessageLog.logMessage(f"->Checking layer: {layer.name()}", PLUGIN_NAME)
            for feat in layer.getFeatures(line.geometry().boundingBox()):
                self.current_features_done += 1
                self.setProgress(
                    self.current_features_done * 100 // self.total_features
                )
                if self.isCanceled():
                    return False
                if feat.geometry().intersects(line.geometry()):
                    points, length, area = self.analyse_intersections(feat, line)
                    results.append(
                        {
                            "prospect_layer": self.prospect_layer,
                            "prospect_feature": line,
                            "layer": layer,
                            "feature": feat,
                            "intersections": points,
                            "length": length,
                            "area": area,
                        }
                    )
                    QgsMessageLog.logMessage(
                        f"layer: {layer.name()} - No intersections: {points} - Feature ID: {feat.id()}",
                        PLUGIN_NAME,
                        Qgis.MessageLevel.Info,
                    )
        return results

    def analyse_intersections(self, feat, line):
        """Returns the length, area and number of intersections of feat and line"""
        intersection = feat.geometry().intersection(line.geometry())
        int_type = QgsWkbTypes.displayString(intersection.wkbType())
        points = 1
        length = 0
        area = 0
        if "Polygon" in int_type:
            points = len(intersection.asGeometryCollection())
            area = intersection.area()
        if "Line" in int_type:
            points = len(intersection.asGeometryCollection())
            length = intersection.length()
        elif "Point" in int_type:
            points = len(list(intersection.vertices()))
        return points, length, area
