"""Plugin Selection Dialog."""

import qgis.utils
from qgis.core import QgsProject, QgsSymbolLayerUtils, QgsVectorLayer
from qgis.PyQt import uic
from qgis.PyQt.QtCore import QSize, Qt
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QDialog, QTreeWidgetItem, QWidget

from .tools import filter_search_layers, plugin_path

LAYER_PROSPECT_CLASS = uic.loadUiType(str(plugin_path("LayerProspect.ui")))[0]
LAYER_ATTR_TREE_CLASS = uic.loadUiType(str(plugin_path("LayerAttrMap.ui")))[0]


class LayerSelectionDialog(QDialog, LAYER_PROSPECT_CLASS):
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


class LayerSelectionTree(QDialog, LAYER_ATTR_TREE_CLASS):
    """Plugin Layer and Attribute Selection Dialog."""

    def __init__(
        self,
        parent: QWidget,
        layers: tuple[QgsVectorLayer.VectorLayer],
        layer_attr_map: dict[str, tuple[bool, dict[str, bool]]],
    ):
        super().__init__(parent)
        self.setupUi(self)
        self.layers = layers

        for layer in self.layers:
            parent = QTreeWidgetItem(self.treeWidget)
            parent.setText(0, layer.name())
            parent.setFlags(parent.flags() | Qt.ItemIsUserCheckable)
            if layer_attr_map.get(layer.name(), (False, None))[0]:
                parent.setCheckState(0, Qt.Checked)
            else:
                parent.setCheckState(0, Qt.Unchecked)
            for attr in layer.attributeAliases().keys():
                child = QTreeWidgetItem(parent)
                child.setFlags(child.flags() | Qt.ItemIsUserCheckable)
                child.setText(0, attr)
                if layer_attr_map.get(layer.name(), (False, {}))[1].get(attr, False):
                    child.setCheckState(0, Qt.Checked)
                else:
                    child.setCheckState(0, Qt.Unchecked)

    def get_items(self) -> dict[str, tuple[bool, dict[str, bool]]]:
        layer_attr_map = dict()
        root = self.treeWidget.invisibleRootItem()
        signal_count = root.childCount()
        for i in range(signal_count):
            signal = root.child(i)
            attr = dict()
            num_children = signal.childCount()
            for n in range(num_children):
                child = signal.child(n)
                attr[child.text(0)] = child.checkState(0) == Qt.Checked
            layer_attr_map[signal.text(0)] = (signal.checkState(0) == Qt.Checked, attr)
        return layer_attr_map
