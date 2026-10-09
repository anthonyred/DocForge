"""Test a fixed-width table geometry against the selected LibreOffice renderer."""

from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile
import xml.etree.ElementTree as ET


SOURCE = Path(r"D:\DocForge\.visual_validation\generated2.docx")
OUTPUT = Path(r"D:\DocForge\.visual_validation\table_probe.docx")
NS = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
ET.register_namespace("w", NS[1:-1])


def patch_table(root: ET.Element) -> None:
    for table in root.findall(f".//{NS}tbl"):
        properties = table.find(f"{NS}tblPr")
        if properties is None:
            continue
        style = properties.find(f"{NS}tblStyle")
        if style is None:
            style = ET.SubElement(properties, f"{NS}tblStyle")
        style.set(f"{NS}val", "TableGrid")
        width = properties.find(f"{NS}tblW")
        if width is None:
            width = ET.SubElement(properties, f"{NS}tblW")
        width.set(f"{NS}type", "dxa")
        width.set(f"{NS}w", "7920")
        layout = properties.find(f"{NS}tblLayout")
        if layout is None:
            layout = ET.SubElement(properties, f"{NS}tblLayout")
        layout.set(f"{NS}type", "fixed")
        for row in table.findall(f"{NS}tr"):
            for cell, cell_width in zip(row.findall(f"{NS}tc"), (2640, 2640, 2640)):
                cell_properties = cell.find(f"{NS}tcPr")
                if cell_properties is None:
                    cell_properties = ET.SubElement(cell, f"{NS}tcPr")
                cell_width_node = cell_properties.find(f"{NS}tcW")
                if cell_width_node is None:
                    cell_width_node = ET.SubElement(cell_properties, f"{NS}tcW")
                cell_width_node.set(f"{NS}type", "dxa")
                cell_width_node.set(f"{NS}w", str(cell_width))


with ZipFile(SOURCE) as source, ZipFile(OUTPUT, "w", ZIP_DEFLATED) as target:
    for item in source.infolist():
        data = source.read(item.filename)
        if item.filename == "word/document.xml":
            document_xml = ET.fromstring(data)
            patch_table(document_xml)
            data = ET.tostring(document_xml, encoding="utf-8", xml_declaration=True)
        target.writestr(item, data)
