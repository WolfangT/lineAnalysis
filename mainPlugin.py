"""LineAnalysis main entry point for setting up the UI, Processing."""

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
from .tools import plugin_path, PLUGIN_NAME
from .PluginSelectionDialog import LayerSelectionDialog


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
        self.menu = self.iface.pluginMenu().addMenu(self.icon, "&Line Analysis")
        self.menu.addAction(self.action)
        # self.iface.addToolBarIcon(self.action)
        # self.iface.addPluginToMenu("&Line Analysis", self.action)

        # connect to signal renderComplete which is emitted when canvas
        # rendering is done
        self.iface.mapCanvas().renderComplete.connect(self.renderTest)

    def unload(self):
        # remove the plugin menu item and icon
        self.iface.removePluginMenu("&Line Analysis", self.action)
        self.iface.removeToolBarIcon(self.action)

        # disconnect form signal of the canvas
        self.iface.mapCanvas().renderComplete.disconnect(self.renderTest)

    def run(self):
        # create and show a configuration dialog or something similar
        if QgsProject.instance().fileName() == "":
            return
        dlg = LayerSelectionDialog(self.iface.mainWindow())
        dlg.exec()
        if dlg.result():
            prospect_layer_name = dlg.comboPlugin.currentText()
            analise_layer(prospect_layer_name)

    def renderTest(self, painter):
        # use painter for drawing to map canvas
        print("TestPlugin: renderTest called!")
