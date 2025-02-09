"""helper functions"""

from pathlib import Path

from qgis.core import QgsVectorLayer, QgsProject

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
