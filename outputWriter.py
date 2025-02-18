"""outputWriter.py

Module for diferent clasess of output formats
"""

import csv
import sys
from datetime import date, datetime
from time import sleep

from qgis.core import *
from qgis.PyQt.QtCore import QDate, QDateTime, QVariant

from .tools import PLUGIN_NAME, get_excel_cols, get_feature_attributes, plugin_path

# import_path = plugin_path("./venv/lib/python3.13/site-packages")
# sys.path.insert(0, import_path)
# from openpyxl import Workbook
# from openpyxl.styles import (Alignment, Border, Font, PatternFill, Protection,
#                              Side)

# Classes


class WriteCSVTask(QgsTask):
    """Task that creates and cleans a csv file"""

    def __init__(self, folder, results, layers_attributes_map):
        super().__init__("Creating and Cleaning CSV")
        for i in range(1, 1000):
            filename = folder / f"output_{i}.csv"
            if not filename.exists():
                break
        self.filename = filename
        self.results = results
        self.layers_attributes_map = layers_attributes_map

    def run(self):
        QgsMessageLog.logMessage(
            f"Started task {self.description()}",
            PLUGIN_NAME,
            Qgis.Success,
        )
        fieldnames, rows = self.get_csv_fieldnames_and_rows()
        with open(self.filename, "w", newline="") as csvfile:
            writer = csv.DictWriter(
                csvfile,
                fieldnames=fieldnames.keys(),
                dialect="excel",
                extrasaction="ignore",
            )
            writer.writeheader()
            for row in rows:
                writer.writerow(row)
        return True

    def finished(self, result):
        QgsMessageLog.logMessage(
            f"Output written to {self.filename}",
            PLUGIN_NAME,
            Qgis.Success,
        )

    def clean(self, attributes):
        for key, value in attributes.items():
            if type(value) in (date, datetime):
                attributes[key] = value.isoformat()
            # elif type(value) is float:
            #     attributes[key] = str(value).replace(".", ",")
            #     attributes[key] = str(round(value, 2))
            #     attributes[key] = str(value)
        return attributes

    def get_csv_fieldnames_and_rows(self):
        fieldnames = {
            "qgis_prospect_line": True,
            "qgis_layer": True,
            "qgis_feature_id": True,
            "intersections (No)": True,
            "length (km)": True,
            "area (ha)": True,
        }
        total = len(self.results)
        layers = []
        for i, result in enumerate(self.results):
            self.setProgress(i * 10 / total)
            if self.isCanceled():
                return False
            if result["layer"] not in layers:
                layer = result["layer"]
                layers.append(layer)
                layer_valid, attrs = self.layers_attributes_map.get(
                    layer.name(), (False, {})
                )
                if not layer_valid:
                    continue
                for attr, valid in attrs.items():
                    if valid and attr not in fieldnames:
                        fieldnames[attr] = False
                # else:
                #     for attr in list(layer.attributeAliases().keys()):
                #         if attr not in fieldnames:
                #             fieldnames[attr] = False
        rows = []
        for i, result in enumerate(self.results):
            self.setProgress(10 + i * 90 / total)
            if self.isCanceled():
                return False
            line = result["prospect_feature"].attributeMap().get("name")
            if line is None or (type(line) is QVariant and line.isNull()):
                line = result["prospect_feature"].id()
            data = self.clean(
                {
                    "qgis_prospect_line": line,
                    "qgis_layer": result["layer"].name().split(" — ")[0],
                    "qgis_feature_id": result["feature"].id(),
                    "intersections (No)": result["intersections"],
                    "length (km)": result["length"] / 1000,
                    "area (ha)": result["area"] / 10000,
                }
                | get_feature_attributes(result["feature"])
            )
            for key, value in data.items():
                if key in fieldnames:
                    if not fieldnames[key] and value:
                        fieldnames[key] = True
            rows.append(data)
        to_delete = []
        for key, has_value in fieldnames.items():
            if not has_value:
                to_delete.append(key)
        for key in to_delete:
            del fieldnames[key]
        return fieldnames, rows


# class WriteXLSX(QgsTask):
#     """Task that creates and cleans an Excel file"""

#     font_general = Font(
#         name="Calibri",
#         size=11,
#         bold=False,
#         italic=False,
#         vertAlign=None,
#         underline="none",
#         strike=False,
#         color="FF000000",
#     )

#     font_title = Font(
#         name="Calibri",
#         size=11,
#         bold=True,
#         italic=False,
#         vertAlign=None,
#         underline="none",
#         strike=False,
#         color="FF000000",
#     )

#     alignment_general = Alignment(
#         horizontal="left",
#         vertical="center",
#         text_rotation=0,
#         wrap_text=True,
#         shrink_to_fit=True,
#         indent=0,
#     )

#     alignment_center = Alignment(
#         horizontal="center",
#         vertical="center",
#         text_rotation=0,
#         wrap_text=True,
#         shrink_to_fit=True,
#         indent=0,
#     )

#     estilos = {
#         "general": alignment_general,
#         "center": alignment_center,
#     }

#     def __init__(self, filename, results, layers_attributes_map):
#         super().__init__("Creating and Cleaning an Excel file")
#         self.filename = filename
#         self.results = results
#         self.layers_attributes_map = layers_attributes_map

#     def run(self):
#         fieldnames = {
#             "qgis_prospect_line": [10, "center", True],
#             "qgis_layer": [25, "center", True],
#             "qgis_feature_id": [10, "center", True],
#             "intersections (No)": [10, "general", True],
#             "length (km)": [10, "general", True],
#             "area (ha)": [10, "general", True],
#         }
#         total = len(self.results)
#         layers = []
#         for i, result in enumerate(self.results):
#             self.setProgress(i * 45 / total)
#             if self.isCanceled():
#                 return False
#             if result["layer"] not in layers:
#                 layer = result["layer"]
#                 layers.append(layer)
#                 if layer.name() in self.layers_attributes_map:
#                     for attr in self.layers_attributes_map[layer.name()]:
#                         if attr not in fieldnames:
#                             fieldnames[attr] = [10, "general", False]
#                 else:
#                     for attr in list(layer.attributeAliases().keys()):
#                         if attr not in fieldnames:
#                             fieldnames[attr] = [10, "general", False]
#         wb = Workbook()
#         normal = wb._named_styles["Normal"]
#         normal.alignment.wrap_text = True
#         normal.alignment.vertical = "center"
#         normal.alignment.shrink_to_fit = True
#         normal.font = self.font_general
#         ws = wb.active
#         wb.alignment = self.alignment_general
#         ws.append(list(fieldnames))
#         for i, result in enumerate(self.results):
#             self.setProgress(45 + i * 45 / total)
#             if self.isCanceled():
#                 return False
#             line = result["prospect_feature"].attributeMap().get("name")
#             if line is None or (type(line) is QVariant and line.isNull()):
#                 line = result["prospect_feature"].id()
#             data = {
#                 "qgis_prospect_line": line,
#                 "qgis_layer": result["layer"].name().split(" — ")[0],
#                 "qgis_feature_id": result["feature"].id(),
#                 "intersections (No)": result["intersections"],
#                 "length (km)": result["length"],
#                 "area (ha)": result["area"],
#             } | get_feature_attributes(result["feature"])
#             for key, value in data.items():
#                 if key in fieldnames:
#                     if value:
#                         fieldnames[key][0] = max(len(str(value)), fieldnames[key][0])
#                         fieldnames[key][2] = True
#             try:
#                 ws.append([data.get(field) for field in fieldnames])
#             except ValueError as err:
#                 print([data.get(field) for field in fieldnames])
#                 print(err)
#         # extras
#         to_delete = []
#         for i, (col, (size, alin, has_value)) in enumerate(
#             zip(get_excel_cols(), fieldnames.values())
#         ):
#             ws.column_dimensions[col].width = size or 10
#             ws.column_dimensions[col].alignment = self.estilos[alin]
#             if not has_value:
#                 to_delete.append((i, col))
#         filters = ws.auto_filter
#         filters.ref = f"A:{col}"
#         total = len(to_delete)
#         for i, (n, col) in enumerate(to_delete[::-1]):
#             self.setProgress(90 + i * 10 / total)
#             if self.isCanceled():
#                 return False
#             # ws.delete_cols(n + 1)
#             ws.column_dimensions[col].hidden = True
#         ws.row_dimensions[1].font = self.font_title
#         # save
#         wb.save(self.filename)
#         return True

#     def finished(self, result):
#         QgsMessageLog.logMessage(
#             f"Output written to {self.filename}",
#             PLUGIN_NAME,
#             Qgis.Success,
#         )
