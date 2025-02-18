"""helper functions"""

import string
from pathlib import Path

from qgis.core import QgsProject, QgsVectorLayer
from qgis.PyQt.QtCore import QDate, QDateTime, QVariant

# Constans

PLUGIN_NAME = "Line Analysis"

# functions


def plugin_path(*args):
    """Get the path to plugin root folder."""
    path = Path(__file__).parent
    for item in args:
        path = path / item
    return path.absolute()


def filter_search_layers(layers, prospect_layer=None):
    """Only returns layers that are visible, Vectorial and not the proscpect layer"""
    layer_tree_root = QgsProject.instance().layerTreeRoot()
    for layer in layers:
        layer_tree_layer = layer_tree_root.findLayer(layer)
        if (
            layer is prospect_layer
            or layer.type() != QgsVectorLayer.VectorLayer
            or not layer_tree_layer.isVisible()
        ):
            continue
        yield layer


def filter_features(features):
    """only returns valid features to make analysis"""
    for feature in features:
        if feature.isValid():
            yield feature


def get_prospect_layer(layers, prospect_layer_name):
    for layer in layers:
        if layer.name() == prospect_layer_name:
            if layer.type() == QgsVectorLayer.VectorLayer:
                return layer
            else:
                raise ValueError("Prospect layer must be a VectorLayer")
    raise ValueError("No prospect layer found")


def get_feature_attributes(feature):
    attr_map = feature.attributeMap()
    for key, value in attr_map.copy().items():
        if value is None:
            del attr_map[key]
        if str(value).strip() in ("NULL", ""):
            del attr_map[key]
        elif type(value) is QVariant and value.isNull():
            del attr_map[key]
        elif type(value) is QDate:
            attr_map[key] = value.toPyDate()
            # attr_map[key] = value.toString("dd/MM/yyyy")
        elif type(value) is QDateTime:
            # attr_map[key] = value.toString("dd/MM/yyyy HH:mm:ss")
            attr_map[key] = value.toPyDateTime()
    return attr_map


def get_excel_cols():
    for l in string.ascii_uppercase:
        yield l
    for l1 in string.ascii_uppercase:
        for l2 in string.ascii_uppercase:
            yield l1 + l2
    for l1 in string.ascii_uppercase:
        for l2 in string.ascii_uppercase:
            for l3 in string.ascii_uppercase:
                yield l1 + l2 + l3
