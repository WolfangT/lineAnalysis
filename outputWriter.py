"""outputWriter.py

Module for diferent clasess of output formats
"""

import csv
from time import sleep

from qgis.core import *
from qgis.PyQt.QtCore import QDateTime, QDate, QVariant

from .tools import PLUGIN_NAME


# Classes


class writeCSVTask(QgsTask):
    """Task that creates and cleans a csv file"""

    def __init__(
        self,
        filename,
        results,
    ):
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
                    | self.get_feature_attributes(result["feature"])
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
