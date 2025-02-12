"""outputWriter.py

Module for diferent clasess of output formats
"""

import csv
import sys
from time import sleep

from qgis.core import *
from qgis.PyQt.QtCore import QVariant

from .tools import PLUGIN_NAME, get_feature_attributes, plugin_path, get_excel_cols

import_path = plugin_path("./venv/lib/python3.13/site-packages")
sys.path.insert(0, import_path)
from openpyxl import Workbook
from openpyxl.styles import PatternFill, Border, Side, Alignment, Protection, Font


# Classes


class WriteCSVTask(QgsTask):
    """Task that creates and cleans a csv file"""

    def __init__(self, filename, results):
        super().__init__("Creating and Cleaning CSV")
        self.filename = filename
        self.results = results

    def run(self):
        QgsMessageLog.logMessage(
            f"Started task {self.description()}",
            PLUGIN_NAME,
            Qgis.Success,
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
                        "qgis_feature_id": result["feature"].id(),
                        "#_of_intersections": result["intersections"],
                        "length": result["length"],
                        "area": result["area"],
                    }
                    | get_feature_attributes(result["feature"])
                )
        return True

    def finished(self, result):
        QgsMessageLog.logMessage(
            f"Output written to {self.filename}",
            PLUGIN_NAME,
            Qgis.Success,
        )

    def get_csv_fieldnames(self):
        fieldnames = [
            "qgis_prospect_layer",
            "qgis_prospect_feature_id",
            "qgis_layer",
            "qgis_feature_id",
            "#_of_intersections",
            "length",
            "area",
        ]
        layer = None
        for result in self.results:
            if not result["layer"] is layer:
                layer = result["layer"]
                for attr in list(layer.attributeAliases().keys()):
                    if attr not in fieldnames:
                        fieldnames.append(attr)
        working_fieldnames = fieldnames[7:]
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


class WriteCSVTask2(QgsTask):
    """Task that creates and cleans a csv file"""

    def __init__(self, filename, results):
        super().__init__("Creating and Cleaning CSV")
        self.filename = filename
        self.results = results

    def run(self):
        QgsMessageLog.logMessage(
            f"Started task {self.description()}",
            PLUGIN_NAME,
            Qgis.Success,
        )
        fieldnames = (
            "qgis_prospect_line",
            "qgis_layer",
            "qgis_feature_id",
            "intersections (No)",
            "length (km)",
            "area (ha)",
            "properties",
        )
        total = len(self.results)
        p_layer = None
        total_points = 0
        total_length = 0
        total_area = 0
        with open(self.filename, "w", newline="") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for i, result in enumerate(self.results):
                self.setProgress(i * 100 / total)
                if self.isCanceled():
                    return False
                if not result["layer"] is p_layer:
                    if not p_layer is None:
                        writer.writerow(
                            {
                                "qgis_prospect_line": result["prospect_feature"]
                                .attributeMap()
                                .get("name", result["prospect_feature"].id()),
                                "qgis_layer": f"Total - {p_layer.name().split(" — ")[0]}",
                                "intersections (No)": total_points,
                                "length (km)": round(total_length, 3),
                                "area (ha)": round(total_area, 4),
                            }
                        )
                        total_points = 0
                        total_length = 0
                        total_area = 0
                    p_layer = result["layer"]
                total_points += result["intersections"]
                total_length += result["length"]
                total_area += result["area"]
                writer.writerow(
                    {
                        "qgis_prospect_line": result["prospect_feature"]
                        .attributeMap()
                        .get("name", result["prospect_feature"].id()),
                        "qgis_layer": result["layer"].name().split(" — ")[0],
                        "qgis_feature_id": result["feature"].id(),
                        "intersections (No)": result["intersections"],
                        "length (km)": result["length"],
                        "area (ha)": result["area"],
                        "properties": self.create_properties_string(result["feature"]),
                    }
                )
        return True

    def finished(self, result):
        QgsMessageLog.logMessage(
            f"Output written to {self.filename}",
            PLUGIN_NAME,
            Qgis.Success,
        )

    def create_properties_string(self, feature):
        data = get_feature_attributes(feature)
        string = ""
        for key, value in data.items():
            string += f"{key}: {value}, "
        return string


class WriteXLSX(QgsTask):
    """Task that creates and cleans an Excel file"""

    font_general = Font(
        name="Calibri",
        size=11,
        bold=False,
        italic=False,
        vertAlign=None,
        underline="none",
        strike=False,
        color="FF000000",
    )

    font_title = Font(
        name="Calibri",
        size=11,
        bold=True,
        italic=False,
        vertAlign=None,
        underline="none",
        strike=False,
        color="FF000000",
    )

    alignment_general = Alignment(
        horizontal="left",
        vertical="center",
        text_rotation=0,
        wrap_text=True,
        shrink_to_fit=True,
        indent=0,
    )

    alignment_center = Alignment(
        horizontal="center",
        vertical="center",
        text_rotation=0,
        wrap_text=True,
        shrink_to_fit=True,
        indent=0,
    )

    estilos = {
        "general": alignment_general,
        "center": alignment_center,
    }

    def __init__(self, filename, results, layers_attributes_map):
        super().__init__("Creating and Cleaning an Excel file")
        self.filename = filename
        self.results = results
        self.layers_attributes_map = layers_attributes_map

    def run(self):
        fieldnames = {
            "qgis_prospect_line": [10, "center", True],
            "qgis_layer": [25, "center", True],
            "qgis_feature_id": [10, "center", True],
            "intersections (No)": [10, "general", True],
            "length (km)": [10, "general", True],
            "area (ha)": [10, "general", True],
        }
        total = len(self.results)
        layers = []
        for i, result in enumerate(self.results):
            self.setProgress(i * 30 / total)
            if self.isCanceled():
                return False
            if result["layer"] not in layers:
                layer = result["layer"]
                layers.append(layer)
                if layer.name() in self.layers_attributes_map:
                    for attr in self.layers_attributes_map[layer.name()]:
                        if attr not in fieldnames:
                            fieldnames[attr] = [10, "general", False]
                else:
                    for attr in list(layer.attributeAliases().keys()):
                        if attr not in fieldnames:
                            fieldnames[attr] = [10, "general", False]
        wb = Workbook()
        normal = wb._named_styles["Normal"]
        normal.alignment.wrap_text = True
        normal.alignment.vertical = "center"
        normal.alignment.shrink_to_fit = True
        normal.font = self.font_general
        ws = wb.active
        wb.alignment = self.alignment_general
        ws.append(list(fieldnames))
        for i, result in enumerate(self.results):
            self.setProgress(30 + i * 30 / total)
            if self.isCanceled():
                return False
            data = {
                "qgis_prospect_line": result["prospect_feature"]
                .attributeMap()
                .get("name", result["prospect_feature"].id()),
                "qgis_layer": result["layer"].name().split(" — ")[0],
                "qgis_feature_id": result["feature"].id(),
                "intersections (No)": result["intersections"],
                "length (km)": result["length"],
                "area (ha)": result["area"],
            } | get_feature_attributes(result["feature"])
            for key, value in data.items():
                if key in fieldnames:
                    if value:
                        fieldnames[key][0] = max(len(str(value)), fieldnames[key][0])
                        fieldnames[key][2] = True
            ws.append([data.get(field) for field in fieldnames])
        # extras
        to_delete = []
        for i, (col, (size, alin, has_value)) in enumerate(
            zip(get_excel_cols(), fieldnames.values())
        ):
            ws.column_dimensions[col].width = size or 10
            ws.column_dimensions[col].alignment = self.estilos[alin]
            if not has_value:
                to_delete.append(i)
        total = len(to_delete)
        for i, col in enumerate(to_delete[::-1]):
            self.setProgress(60 + i * 40 / total)
            if self.isCanceled():
                return False
            ws.delete_cols(col + 1)
        filters = ws.auto_filter
        for i, col in zip(range(len(fieldnames) - len(to_delete)), get_excel_cols()):
            pass
        filters.ref = f"A:{col}"
        ws.row_dimensions[1].font = self.font_title
        # save
        wb.save(self.filename)
        return True

    def finished(self, result):
        QgsMessageLog.logMessage(
            f"Output written to {self.filename}",
            PLUGIN_NAME,
            Qgis.Success,
        )
