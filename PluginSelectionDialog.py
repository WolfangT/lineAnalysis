"""Plugin Selection Dialog."""

from qgis.core import QgsProject, QgsSymbolLayerUtils
from qgis.PyQt import uic
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtCore import QSize
from qgis.PyQt.QtWidgets import QDialog, QWidget
import qgis.utils

from .tools import plugin_path, filter_search_layers


FORM_CLASS = uic.loadUiType(str(plugin_path("PluginSelectionDialogBase.ui")))[0]


class LayerSelectionDialog(QDialog, FORM_CLASS):
    """Plugin Selection Window."""

    def __init__(self, parent: QWidget):
        """Pseudoconstructor."""
        super().__init__(parent)
        self.setupUi(self)

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
