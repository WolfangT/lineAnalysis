"""LineAnalysis main entry point for setting up the UI, Processing."""

from pathlib import Path
import json

from qgis.core import *
from qgis.PyQt import uic
from qgis.PyQt.QtCore import QSize, Qt
from qgis.PyQt.QtGui import *
from qgis.PyQt.QtWidgets import *
from qgis.PyQt.QtWidgets import QAction, QDialog

from .lineAnalysis import CheckIntersections
from .outputWriter import WriteCSVTask
from .pluginUI import LayerSelectionDialog, LayerSelectionTree
from .tools import PLUGIN_NAME, filter_search_layers, get_prospect_layer, plugin_path

# main class

LAYERS_ATTRIBUTES_MAP = {
    "Towers": ("TOWER_ASSE", "ACTION_DTT", "STATUS", "LINE_SERIE", "TOWER_CONS"),
    "CABLE": ("OPERATING_", "STATUS", "CABLE_TYPE", "CABLE_SET", "CABLE_ROUT"),
    "OHL": ("Towers_In", "STATUS", "OPERATING_", "CIRCUIT1", "CIRCUIT2"),
    "AC6 Roads — ac6_test__featureclasstofeatureclass_infrastructure_roadlink": (
        "class",
        "roadNumber",
        "name1",
        "name2",
        "formOfWay",
        "function",
    ),
    "Railways+20m — buffered": ("id",),
}


class lineAnalisisPlugin:
    """Plugin Line Analysis."""

    def __init__(self, iface):
        # save reference to the QGIS interface
        self.iface = iface

    def initGui(self):
        """Init the user interface."""
        self.icon = QIcon(str(plugin_path("icon.png")))
        # create action
        self.action = QAction(self.icon, "Analysis Lines", self.iface.mainWindow())
        self.action.setObjectName("Analysis Lines")
        self.action.setWhatsThis("Run Line Analysis")
        self.action.setStatusTip("Line Analysis Running")
        self.action.triggered.connect(self.run)
        # add toolbar button and menu item
        self.iface.pluginMenu().addAction(self.action)

    def unload(self):
        # remove the plugin menu item and icon
        self.iface.pluginMenu().removeAction(self.action)

    def run(self):
        # Check that there is a file open
        if QgsProject.instance().fileName() == "":
            self.iface.messageBar().pushMessage(
                title=f"{PLUGIN_NAME} Error",
                text="No saved project open",
                level=Qgis.Critical,
                duration=10,
            )
            return False
        # Selects a layer from the TreeView to be the prospect layer
        selected_layers = self.iface.layerTreeView().selectedLayers()
        try:
            prospect_layer = self.select_layer(selected_layers)
        except Exception as err:
            print(err)
            self.iface.messageBar().pushMessage(
                title=f"{PLUGIN_NAME} Error",
                text=str(err),
                level=Qgis.Critical,
                duration=0,
            )
            return False
        # get posible layers to check intersecsions on
        layers = tuple(
            filter_search_layers(
                QgsProject.instance().mapLayers().values(),
                prospect_layer,
            )
        )
        # get layer/attributes map
        try:
            layer_attr_map = self.get_layer_attributes(layers)
        except Exception as err:
            print(err)
            self.iface.messageBar().pushMessage(
                title=f"{PLUGIN_NAME} Error",
                text=str(err),
                level=Qgis.Critical,
                duration=0,
            )
            return False
        # Task execution
        self.main_task = CheckIntersections(layers, prospect_layer, layer_attr_map)
        self.main_task.taskCompleted.connect(self.on_main_task_completed)
        QgsApplication.taskManager().addTask(self.main_task)

    def on_main_task_completed(self):
        self.iface.messageBar().pushMessage(
            title=f"{PLUGIN_NAME} Info",
            text=f"Analysis Complete, Creating and Cleaning Report",
            level=Qgis.Success,
            duration=-1,
        )
        # Get a available filename
        folder = Path(QgsProject.instance().fileName()).parent
        self.output_task = WriteCSVTask(
            folder, self.main_task.results, self.main_task.layer_attr_map
        )
        self.output_task.taskCompleted.connect(self.on_output_task_completed)
        QgsApplication.taskManager().addTask(self.output_task)

    def on_output_task_completed(self):
        self.iface.messageBar().pushMessage(
            title=f"{PLUGIN_NAME} Info",
            text=f"Output written to {self.output_task.filename}",
            level=Qgis.Success,
            duration=0,
        )

    def select_layer(
        self, layers: tuple[QgsVectorLayer.VectorLayer]
    ) -> QgsVectorLayer.VectorLayer:
        """Returns the selected layer name, from the TreeView or the dialog"""
        if len(layers) != 1:
            dlg = LayerSelectionDialog(self.iface.mainWindow())
            dlg.exec()
            if dlg.result():
                return get_prospect_layer(layers, dlg.comboPlugin.currentText())
        else:
            return get_prospect_layer(layers, layers[0].name())

    def get_layer_attributes(
        self, layers: tuple[QgsVectorLayer.VectorLayer]
    ) -> dict[str, tuple[bool, dict[str, bool]]]:
        """Gets a map of layers:attributes list for the output"""
        layer_attr_map_file = (
            Path(QgsProject.instance().fileName()).parent / "layer_attr_map.json"
        )
        layer_attr_map = {}
        if layer_attr_map_file.exists():
            try:
                with layer_attr_map_file.open("r") as _file:
                    layer_attr_map = json.load(_file)
            except Exception as err:
                print(err)
                self.iface.messageBar().pushMessage(
                    title=f"{PLUGIN_NAME} Error",
                    text=f"Error on loading layer/attributes map file: {err}",
                    level=Qgis.Critical,
                    duration=-1,
                )
                raise err
        dlg = LayerSelectionTree(self.iface.mainWindow(), layers, layer_attr_map)
        dlg.exec()
        if dlg.result():
            layer_attr_map = dlg.get_items()
            try:
                with layer_attr_map_file.open("w") as _file:
                    json.dump(layer_attr_map, _file, indent=2)
            except Exception as err:
                print(err)
                self.iface.messageBar().pushMessage(
                    title=f"{PLUGIN_NAME} Error",
                    text=f"Error on writing layer/attributes map file: {err}",
                    level=Qgis.Critical,
                    duration=-1,
                )

                raise err
            return layer_attr_map
