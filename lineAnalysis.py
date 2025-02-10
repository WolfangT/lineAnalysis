"""lineAnalysis.py

Script for checking intersection between lines
"""

from qgis.core import *

from .tools import filter_search_layers, filter_features, PLUGIN_NAME


# functions


def analyse_intersections(feat, line):
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


def check_intersections(layers, prospect_layer, line):
    """Checks intersections on a feature from other layers"""
    results = []
    QgsMessageLog.logMessage(f"-> Analising Feature with ID: {line.id()}", PLUGIN_NAME)
    for layer in filter_search_layers(layers, prospect_layer):
        QgsMessageLog.logMessage(f"->Checking layer: {layer.name()}", PLUGIN_NAME)
        for feat in layer.getFeatures(line.geometry().boundingBox()):
            if feat.geometry().intersects(line.geometry()):
                points, length, area = analyse_intersections(feat, line)
                results.append(
                    {
                        "prospect_layer": prospect_layer,
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


# main function


def analise_layer(layers, prospect_layer):
    results = []
    QgsMessageLog.logMessage(
        "-" * 50 + f"\nSearching collisions for layer: {prospect_layer.name()}",
        PLUGIN_NAME,
        level=Qgis.MessageLevel.Success,
    )
    for line in filter_features(prospect_layer.getFeatures()):
        results += check_intersections(layers, prospect_layer, line)
    QgsMessageLog.logMessage(
        f">Finished!\n" + "-" * 50, PLUGIN_NAME, level=Qgis.MessageLevel.Success
    )
    return results
