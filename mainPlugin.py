"""LineAnalysis main entry point for setting up the UI, Processing."""

import csv
from pathlib import Path

from qgis.PyQt.QtGui import *
from qgis.PyQt.QtWidgets import *
from qgis.core import *
from qgis.PyQt import uic
from qgis.PyQt.QtWidgets import (
    QAction,
    QDialog,
    QMenu,
    QLabel,
    QMessageBox,
    QPushButton,
)

from .lineAnalysis import analise_layer
from .tools import plugin_path, PLUGIN_NAME, get_prospect_layer
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

        # connect to signal renderComplete which is emitted when canvas
        # rendering is done
        self.iface.mapCanvas().renderComplete.connect(self.renderTest)

    def unload(self):
        # remove the plugin menu item and icon
        self.iface.pluginMenu().removeAction(self.action)

        # disconnect form signal of the canvas
        self.iface.mapCanvas().renderComplete.disconnect(self.renderTest)

    def run(self):
        # check that there is a file open
        if QgsProject.instance().fileName() == "":
            self.iface.messageBar().pushMessage(
                title=f"{PLUGIN_NAME} Error",
                text="No saved project open",
                level=Qgis.Critical,
                duration=10,
            )
            return

        selected_layers = self.iface.layerTreeView().selectedLayers()
        layers = list(QgsProject.instance().mapLayers().values())

        try:
            prospect_layer = self.select_layer(selected_layers)
        except ValueError as err:
            print(err)
            self.iface.messageBar().pushMessage(
                title=f"{PLUGIN_NAME} Error",
                text=str(err),
                level=Qgis.Critical,
                duration=10,
            )

        results = analise_layer(layers, prospect_layer)
        self.create_csv(results)

    def renderTest(self, painter):
        pass

    def select_layer(self, layers):
        """Returns the selected layer name, from the TreeView or the dialog"""
        if len(layers) != 1:
            dlg = LayerSelectionDialog(self.iface.mainWindow())
            dlg.exec()
            if dlg.result():
                return get_prospect_layer(layers, dlg.comboPlugin.currentText())
        else:
            return get_prospect_layer(layers, layers[0].name())

    def create_csv(self, results):
        filename = Path(QgsProject.instance().fileName()).parent / "output.csv"
        fieldnames = [
            "prospect_layer",
            "prospect_feature_qgis_id",
            "layer",
            "intersections",
            "feature_qgis_id",
        ]
        layer = None
        for result in results:
            if not result["layer"] is layer:
                layer = result["layer"]
                for attr in list(layer.attributeAliases().keys()):
                    fieldnames.append(attr)
        with open(filename, "w", newline="") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for result in results:
                writer.writerow(
                    {
                        "prospect_layer": result["prospect_layer"].name(),
                        "prospect_feature_qgis_id": result["prospect_feature"].id(),
                        "layer": result["layer"].name(),
                        "intersections": result["intersections"],
                        "feature_qgis_id": result["feature"].id(),
                    }
                    | result["feature"].attributeMap()
                )
        self.iface.messageBar().pushMessage(
            title=f"{PLUGIN_NAME} Info",
            text=f"Output written to {filename}",
            level=Qgis.Info,
            duration=10,
        )
