from PySide6.QtGui import *
from PySide6.QtWidgets import *
from PySide6.QtCore import *

import sys
import importlib
from osm import osm
from canvas import Canvas

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setFixedWidth(1728)
        self.setFixedHeight(965)

        projectWatcher = QFileSystemWatcher(self)
        projectWatcher.addPath("render.py")
        projectWatcher.addPath("data.py")
        projectWatcher.addPath("export.py")
        projectWatcher.fileChanged.connect(self.file_changed)
    
        self.render_module = importlib.import_module("render")
        self.data_module = importlib.import_module("data")
        self.export_module = importlib.import_module("export")

        self.selected_node = None
        self.nodes, self.ways, self.relations = osm("map.osm")
        self.zoom, self.lat, self.lon = 17, 47.49001, 19.05665 #at 17th zoom, the correction should be: 47.49610, 19.04914
        self.scale = 5000 * self.zoom
        self.lat -= -0.00609
        self.lon -= 0.00751

        file_menu = self.menuBar().addMenu("File")
        export_menu = file_menu.addAction("Export")
        export_menu.triggered.connect(self.export)

        view_menu = self.menuBar().addMenu("View")
        self.editor_menu = view_menu.addAction("Editor")
        self.editor_menu.setCheckable(True)
        self.editor_menu.setChecked(True)
        self.editor_menu.changed.connect(self.editor_visibility_changed)

        self.canvas = Canvas(self)
        self.canvas.setRender(getattr(self.render_module, "render_nodes"), getattr(self.render_module, "render_ways"), getattr(self.render_module, "render_relations"))
        self.canvas.setData(getattr(self.data_module, "filter_nodes")(self.nodes), getattr(self.data_module, "filter_ways")(self.ways), getattr(self.data_module, "filter_relations")(self.relations))
        self.canvas.setCamera(self.lon, self.lat, self.scale)
        self.canvas.setEditorVisible(self.editor_menu.isChecked())
        self.setCentralWidget(self.canvas)


    def file_changed(self, path: str):
        try:
            if "render" in path:
                print("render module is successfully reloaded")
                importlib.reload(self.render_module)
                self.canvas.setRender(getattr(self.render_module, "render_nodes"), getattr(self.render_module, "render_ways"), getattr(self.render_module, "render_relations"))
            elif "data" in path:
                print("data module reloaded")
                importlib.reload(self.data_module)
                self.canvas.setData(getattr(self.data_module, "filter_nodes")(self.nodes), getattr(self.data_module, "filter_ways")(self.ways), getattr(self.data_module, "filter_relations")(self.relations))
                self.canvas.setCamera(self.lon, self.lat, self.scale)
                self.canvas.update()
            elif "export" in path:
                print("export module reloaded")
                importlib.reload(self.export_module)
        except Exception as e:
            print(e)
    
    def editor_visibility_changed(self):
        self.canvas.setEditorVisible(self.editor_menu.isChecked())
        self.canvas.update()

    def export(self):
        getattr(self.export_module, "export")(self.lat, self.lon, 5000, self.nodes, self.ways, self.relations)

    
    def mousePressEvent(self, event: QMouseEvent):
        self.last_mouse_position_x = event.position().x()
        self.last_mouse_position_y = event.position().y()
        self.select_node(event.position().x(), event.position().y())
        self.canvas.update()

    def mouseMoveEvent(self, event: QMouseEvent):
        self.delta_mouse_position_x = event.position().x() - self.last_mouse_position_x
        self.delta_mouse_position_y = event.position().y() - self.last_mouse_position_y

        self.lon += -self.delta_mouse_position_x / self.scale
        self.lat += self.delta_mouse_position_y / self.scale
        self.canvas.setCamera(self.lon, self.lat, self.scale)

        self.last_mouse_position_x = event.position().x()
        self.last_mouse_position_y = event.position().y()

        self.canvas.update()
    
    def wheelEvent(self, event: QWheelEvent) -> None:
        self.scale += event.angleDelta().y() * 2
        self.canvas.setCamera(self.lon, self.lat, self.scale)
        self.canvas.update()

    def select_node(self, x, y):
        dis = 1000
        index = -1
        selected_node_index = None
        nodes = getattr(self.data_module, "selectable_nodes")
        for node in nodes:
            index += 1
            d = (node.render_x  - x) * (node.render_x  - x) + \
                (-node.render_y - y) * (-node.render_y - y)
            if dis > d:
                dis = d
                selected_node_index = index

        if selected_node_index:
            if self.selected_node:
                self.selected_node.selected = False
                self.select_parent(self.selected_node, False)
            self.selected_node = nodes[selected_node_index]
            self.selected_node.selected = True
            self.select_parent(self.selected_node, True)
            self.print_selected(self.selected_node)
        else:
            if self.selected_node:
                self.selected_node.selected = False
                self.select_parent(self.selected_node, False)
            

    def select_parent(self, entity, selected):
        if entity.parent:
            entity.parent.selected = selected
            self.select_parent(entity.parent, selected)
        if entity.parent_type == "relation":
            for member in entity.parent.members:
                member.member.secondary_selected = selected
    
    def print_selected(self, node):
        if not node.parent:
            print(f'Node {node.id}')
            for tag in node.tags:
                print(f'k: {tag.k}')
                print(f'v: {tag.v}')
        elif node.parent_type == "way":
            print(f'Way {node.parent.id}')
            for tag in node.parent.tags:
                print(f'k: {tag.k}')
                print(f'v: {tag.v}')
            if node.parent.parent:
                print('---------------------------')
                print(f'Parent relation {node.parent.parent.id}')
                for tag in node.parent.parent.tags:
                    print(f'k: {tag.k}')
                    print(f'v: {tag.v}')
        elif node.parent_type == "relation":
            print(f'Relation {node.parent.id}')
            for tag in node.parent.tags:
                print(f'k: {tag.k}')
                print(f'v: {tag.v}')
        print("==============================")

app = QApplication(sys.argv)

window = MainWindow()
window.show()

app.exec()

