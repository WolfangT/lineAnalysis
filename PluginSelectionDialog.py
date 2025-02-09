"""Plugin Selection Dialog."""

from qgis.core import QgsProject, QgsSymbolLayerUtils, QgsVectorLayer
from qgis.PyQt import uic
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtCore import QSize
from qgis.PyQt.QtWidgets import QDialog, QWidget
import qgis.utils

from .tools import plugin_path, filter_search_layers


FORM_CLASS = uic.loadUiType(str(plugin_path("PluginSelectionDialogBase.ui")))[0]


class LayerSelectionDialog(QDialog, FORM_CLASS):
    """Plugin Layer Selection Window."""

    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self.setupUi(self)
        self.setWindowTitle("Select a Layer")
        self.label.setText("Select the layer you want to check collisions on:")

        project = QgsProject.instance()
        layers = list(project.mapLayers().values())

        for layer in filter_search_layers(layers):
            try:
                icon = QgsSymbolLayerUtils.symbolPreviewIcon(
                    layer.renderer().symbol(), QSize(16, 16)
                )
            except (KeyError, AttributeError):
                icon = QIcon()
            self.comboPlugin.addItem(icon, layer.name())


class FeatureSelectionDialog(QDialog, FORM_CLASS):
    """Plugin Feature Selection Window."""

    def __init__(self, parent: QWidget, prospect_layer: QgsVectorLayer.VectorLayer):
        super().__init__(parent)
        self.setupUi(self)
        self.setWindowTitle("Select a Feature")
        self.label.setText("Select the Feature you want to check collisions on:")
        self.prospect_layer = prospect_layer

        project = QgsProject.instance()
        layers = list(project.mapLayers().values())

        for feature in prospect_layer.getFeatures():
            try:
                icon = QgsSymbolLayerUtils.symbolPreviewIcon(
                    prospect_layer.renderer().symbol(), QSize(16, 16)
                )
            except (KeyError, AttributeError):
                icon = QIcon()
            self.comboPlugin.addItem(icon, repr(feature))
