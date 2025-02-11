"""LineAnalysis main entry point for setting up the UI, Processing."""

from pathlib import Path

from qgis.PyQt.QtGui import *
from qgis.PyQt.QtWidgets import *
from qgis.core import *
from qgis.PyQt import uic
from qgis.PyQt.QtWidgets import QAction

from .lineAnalysis import CheckIntersections
from .outputWriter import WriteCSVTask, WriteCSVTask2
from .tools import plugin_path, PLUGIN_NAME, get_prospect_layer, filter_search_layers
from .PluginSelectionDialog import LayerSelectionDialog, FeatureSelectionDialog


# main class


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
        # Selects a layer from the TreeView
        selected_layers = self.iface.layerTreeView().selectedLayers()
        try:
            prospect_layer = self.select_layer(selected_layers)
        except ValueError as err:
            print(err)
            self.iface.messageBar().pushMessage(
                title=f"{PLUGIN_NAME} Error",
                text=str(err),
                level=Qgis.Critical,
                duration=-1,
            )
            return False
        # get posible layers to check intersecsions on
        layers = tuple(
            filter_search_layers(
                QgsProject.instance().mapLayers().values(),
                prospect_layer,
            )
        )
        # Task execution
        self.main_task = CheckIntersections(layers, prospect_layer)
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
        for i in range(1, 1000):
            filename = Path(QgsProject.instance().fileName()).parent / f"output_{i}.csv"
            if not filename.exists():
                break
        self.output_task = WriteCSVTask2(filename, self.main_task.results)
        self.output_task.taskCompleted.connect(self.on_output_task_completed)
        QgsApplication.taskManager().addTask(self.output_task)

    def on_output_task_completed(self):
        self.iface.messageBar().pushMessage(
            title=f"{PLUGIN_NAME} Info",
            text=f"Output written to {self.output_task.filename}",
            level=Qgis.Success,
            duration=0,
        )

    def select_layer(self, layers):
        """Returns the selected layer name, from the TreeView or the dialog"""
        if len(layers) != 1:
            dlg = LayerSelectionDialog(self.iface.mainWindow())
            dlg.exec()
            if dlg.result():
                return get_prospect_layer(layers, dlg.comboPlugin.currentText())
        else:
            return get_prospect_layer(layers, layers[0].name())
