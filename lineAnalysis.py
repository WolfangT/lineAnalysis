"""lineAnalysis.py

Script for checking intersection between lines
"""

from qgis.core import *

from .tools import filter_search_layers, PLUGIN_NAME


# functions


def get_prospect_layer(layers, prospect_layer_name):
    for layer in layers:
        if layer.name() == prospect_layer_name:
            if layer.type() == QgsVectorLayer.VectorLayer:
                return layer
            else:
                raise Exception("Prospect layer must be a VectorLayer")
    raise Exception("No prospect layer found")


def count_number_of_intersections(feat, line):
    intersection = feat.geometry().intersection(line.geometry())
    int_type = QgsWkbTypes.displayString(intersection.wkbType())
    n_int = 0
    if int_type in ("LineString", "Point"):
        n_int = 1
    elif int_type == "MultiPoint":
        n_int = len(list(intersection.vertices()))
    elif int_type == "MultiLineString":
        n_int = len(list(intersection.vertices())) // 2
    return n_int


def check_intersections(layers, prospect_layer_name, line):
    QgsMessageLog.logMessage(f"-> Analising line: {line['name']}", PLUGIN_NAME)
    print(f"-> Analising line: {line['name']}")
    for layer in filter_search_layers(layers, prospect_layer_name):
        for feat in layer.getFeatures(line.geometry().boundingBox()):
            if feat.geometry().intersects(line.geometry()):
                n_int = count_number_of_intersections(feat, line)
                name = feat.attributeMap().get("name")
                QgsMessageLog.logMessage(
                    f"{name} - layer: {layer.name()} - No intersections: {n_int}",
                    PLUGIN_NAME,
                )
                print(f"{name} - layer: {layer.name()} - No intersections: {n_int}")


# main function


def analise_layer(prospect_layer_name):
    layers = QgsProject.instance().mapLayers().values()
    prospect_layer = get_prospect_layer(layers, prospect_layer_name)
    QgsMessageLog.logMessage(
        "-" * 50 + f"\nSearching collisions for layer: {prospect_layer.name()}",
        PLUGIN_NAME,
    )
    print("-" * 50 + f"\nSearching collisions for layer: {prospect_layer.name()}")
    for line in prospect_layer.getFeatures():
        check_intersections(layers, prospect_layer_name, line)
