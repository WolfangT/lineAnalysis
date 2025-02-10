"""LineAnalysis main entry point for setting up the UI, Processing."""

import csv
from time import sleep
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
from qgis.PyQt.QtCore import QDateTime, QDate, QVariant

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
        self.iface.messageBar().pushMessage(
            title=f"{PLUGIN_NAME} Info",
            text=f"Analysis Complete, Creating and Cleaning Report",
            level=Qgis.Success,
            duration=-1,
        )
        filename = Path(QgsProject.instance().fileName()).parent / "output.csv"
        self.taskCSV = writeCSVTask(filename, results, self.iface)
        QgsApplication.taskManager().addTask(self.taskCSV)

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


class writeCSVTask(QgsTask):

    def __init__(self, filename, results, iface):
        super().__init__("Creating and Cleaning CSV")
        self.filename = filename
        self.results = results
        self.iface = iface

    def run(self):
        QgsMessageLog.logMessage(
            f"Started task {self.description()}", PLUGIN_NAME, Qgis.Success
        )
        fieldnames = self.get_csv_fieldnames()
        if fieldnames is None:
            return False
        with open(self.filename, "w", newline="") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for result in self.results:
                writer.writerow(
                    {
                        "qgis_prospect_layer": result["prospect_layer"].name(),
                        "qgis_prospect_feature_id": result["prospect_feature"].id(),
                        "qgis_layer": result["layer"].name(),
                        "#_of_intersections": result["intersections"],
                        "qgis_feature_id": result["feature"].id(),
                    }
                    | self.get_feature_attributes(result["feature"])
                )
        return True

    def finished(self, result):
        QgsMessageLog.logMessage(
            f"Output written to {self.filename}",
            PLUGIN_NAME,
            Qgis.Success,
        )
        self.iface.messageBar().pushMessage(
            title=f"{PLUGIN_NAME} Info",
            text=f"Output written to {self.filename}",
            level=Qgis.Success,
            duration=-1,
        )

    def get_csv_fieldnames(self):
        fieldnames = [
            "qgis_prospect_layer",
            "qgis_prospect_feature_id",
            "qgis_layer",
            "#_of_intersections",
            "qgis_feature_id",
        ]
        layer = None
        for result in self.results:
            if not result["layer"] is layer:
                layer = result["layer"]
                for attr in list(layer.attributeAliases().keys()):
                    if attr not in fieldnames:
                        fieldnames.append(attr)
        working_fieldnames = fieldnames[5:]
        total = len(working_fieldnames)
        for i, fieldname in enumerate(working_fieldnames):
            self.setProgress(i * 100 // total)
            if self.isCanceled():
                return False
            valid = False
            for result in self.results:
                attr_map = result["feature"].attributeMap()
                if fieldname in attr_map:
                    value = attr_map[fieldname]
                    if not (
                        value is None
                        or str(value).strip() == ""
                        or (type(value) is QVariant and value.isNull())
                    ):
                        valid = True
                        break
            if not valid:
                fieldnames.remove(fieldname)
        return fieldnames

    def get_feature_attributes(self, feature):
        attr_map = feature.attributeMap()
        for key, value in attr_map.copy().items():
            if value is None:
                del attr_map[key]
            if str(value).strip() in ("NULL", ""):
                del attr_map[key]
            elif type(value) is QVariant and value.isNull():
                del attr_map[key]
            elif type(value) is QDate:
                attr_map[key] = value.toString("yyyy-MM-dd")
            elif type(value) is QDateTime:
                attr_map[key] = value.toString("yyyy-MM-dd HH:mm:ss")
        return attr_map


class TestTask(QgsTask):

    def __init__(self):
        super().__init__("test task")

    def run(self):
        wait_time = 1 / 100.0
        for i in range(101):
            sleep(wait_time)
            self.setProgress(i)
            if self.isCanceled():
                return False
        return True
