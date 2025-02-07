"""mapAnalysis.py

Script for checking intersection between lines
"""

from qgis.core import *

# Constants
PROSPECT_LAYER = "prospect_lines"
IGNORE_LAYERS = ['OpenStreetMap', 'ESRI OSM, Original GL Style Sheet']
PLUGIN_NAME = 'mapAnalysis'


# functions

def get_prospect_layer(layers):
    for layer in layers:
        if layer.name() == PROSPECT_LAYER:
            return layer
    else:
        raise Exception("no prospect layer found")

def get_bound_rectangle(line):
    # min_x = None
    # min_y = None
    # max_x = None
    # max_y = None
    # for point in line.geometry().vertices():
    #     if min_x is None or point.x() < min_x:
    #         min_x = point.x()
    #     if min_y is None or point.y() < min_y:
    #         min_y = point.y()
    #     if max_x is None or point.x() > max_x:
    #         max_x = point.x()
    #     if max_y is None or point.y() > min_y:
    #         max_y = point.y()
    # return QgsRectangle(min_x, min_y, max_x, max_y)
    return line.geometry().boundingBox()


def check_intersections(layers, line, rect):
    for layer in layers:
        name = layer.name()
        if name in IGNORE_LAYERS or name == PROSPECT_LAYER:
            continue
        for feat in layer.getFeatures(rect):
            if feat.geometry().intersects(line.geometry()):
                intersection = feat.geometry().intersection(line.geometry())
                int_type = QgsWkbTypes.displayString(intersection.wkbType())
                n_int = 0
                if int_type in ("LineString", "Point"):
                    n_int = 1
                elif int_type == "MultiPoint":
                    n_int = len(list(intersection.vertices()))
                elif int_type == "MultiLineString":
                    n_int = len(list(intersection.vertices()))//2
                QgsMessageLog.logMessage(f"->{feat['name']} - layer: {name} - No intersections: {n_int}", PLUGIN_NAME)
                print(f"->{feat['name']} - layer: {name} - No intersections: {n_int}")

# main function

def main():
    project = QgsProject.instance()
    layers = project.mapLayers().values()
    prospect_layer = get_prospect_layer(layers)
    for line in prospect_layer.getFeatures():
        rect = get_bound_rectangle(line)
        QgsMessageLog.logMessage(f"Analising line: {line['name']}", PLUGIN_NAME)
        print(f"Analising line: {line['name']}")
        check_intersections(layers, line, rect)

# start
main()