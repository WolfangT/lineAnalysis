"""outputWriter.py

Module for diferent clasess of output formats
"""

import csv
from time import sleep

from qgis.core import *
from qgis.PyQt.QtCore import QVariant

from .tools import PLUGIN_NAME, get_feature_attributes


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
