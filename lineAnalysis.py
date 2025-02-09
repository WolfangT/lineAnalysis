"""lineAnalysis.py

Script for checking intersection between lines
"""

from qgis.core import *

from .tools import filter_search_layers, filter_features, PLUGIN_NAME


# functions


def count_number_of_intersections(feat, line):
    intersection = feat.geometry().intersection(line.geometry())
    int_type = QgsWkbTypes.displayString(intersection.wkbType())
    n_int = 1
    if "Line" in int_type:
        n_int = len(list(intersection.vertices())) // 2
    elif "Point" in int_type:
        n_int = len(list(intersection.vertices()))
    return n_int


def check_intersections(layers, prospect_layer, line):
    """Checks intersections on a feature from other layers"""
    results = []
    QgsMessageLog.logMessage(f"-> Analising Feature with ID: {line.id()}", PLUGIN_NAME)
    for layer in filter_search_layers(layers, prospect_layer):
        QgsMessageLog.logMessage(f"->Checking layer: {layer.name()}", PLUGIN_NAME)
        for feat in layer.getFeatures(line.geometry().boundingBox()):
            if feat.geometry().intersects(line.geometry()):
                n_int = count_number_of_intersections(feat, line)
                results.append(
                    {
                        "prospect_layer": prospect_layer,
                        "prospect_feature": line,
                        "layer": layer,
                        "feature": feat,
                        "intersections": n_int,
                    }
                )
                QgsMessageLog.logMessage(
                    f"layer: {layer.name()} - No intersections: {n_int} - {feat.attributeMap()}",
                    PLUGIN_NAME,
                )
    return results


# main function


def analise_layer(layers, prospect_layer):
    results = []
    QgsMessageLog.logMessage(
        "-" * 50 + f"\nSearching collisions for layer: {prospect_layer.name()}",
        PLUGIN_NAME,
    )
    for line in filter_features(prospect_layer.getFeatures()):
        results += check_intersections(layers, prospect_layer, line)
    QgsMessageLog.logMessage(f">Finished!\n" + "-" * 50, PLUGIN_NAME)
    return results
