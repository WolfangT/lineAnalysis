"""helper functions"""

from pathlib import Path

from qgis.core import QgsVectorLayer

# Constans

PLUGIN_NAME = "Line Analysis"

# functions


def plugin_path(*args):
    """Get the path to plugin root folder."""
    path = Path(__file__).parent
    for item in args:
        path = path / item
    return path.absolute()


def filter_search_layers(layers, prospect_layer_name=""):
    for layer in layers:
        if (
            # layer.name() in IGNORE_LAYERS
            layer.name() == prospect_layer_name
            or layer.type() != QgsVectorLayer.VectorLayer
        ):
            continue
        yield layer
