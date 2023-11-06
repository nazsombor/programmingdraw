from PySide6.QtGui import *
from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtWebEngineWidgets import QWebEngineView

import sys
import importlib
from osm import Osm
from canvas import Canvas
from export import export

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # WINDOW
        self.setFixedWidth(1728)
        self.setFixedHeight(965)

        # RENDER
        projectWatcher = QFileSystemWatcher(self)
        projectWatcher.addPath("render.py")
        projectWatcher.fileChanged.connect(self.file_changed)
        self.render_module = importlib.import_module("render")

        # MENU
        file_menu = self.menuBar().addMenu("File")
        self.export_menu = file_menu.addAction("Export")
        self.export_menu.triggered.connect(self.export)
        view_menu = self.menuBar().addMenu("View")
        self.editor_menu = view_menu.addAction("Editor")
        self.editor_menu.setCheckable(True)
        self.editor_menu.setChecked(True)
        self.editor_menu.changed.connect(self.editor_visibility_changed)

        # DATA
        self.selected_node = None
        self.osm = Osm("hungary-latest.osm", 300, 1000)
        lat, lon = 47.4892, 19.0529
        self.data = self.osm.data(lon, lat)
        
        # VIEW
        widget = QWidget(self)
        self.canvas = Canvas(widget)
        self.canvas.setRender(getattr(self.render_module, "render_nodes"), getattr(self.render_module, "render_ways"), getattr(self.render_module, "render_relations"))
        self.canvas.setData(self.data)
        self.canvas.setCamera(lon, lat)
        self.canvas.setEditorVisible(self.editor_menu.isChecked())
        self.web_view = QWebEngineView(widget)
        self.web_view.load(QUrl(f"https://openstreetmap.org/#map=17/{lat}/{lon}"))
        self.web_view.urlChanged.connect(self.url_changed)
        layout = QHBoxLayout()
        layout.addWidget(self.web_view)
        layout.addWidget(self.canvas)
        widget.setLayout(layout)
        self.setCentralWidget(widget)

    def file_changed(self, path: str):
        try:
            importlib.reload(self.render_module)
            self.canvas.setRender(getattr(self.render_module, "render_nodes"), getattr(self.render_module, "render_ways"), getattr(self.render_module, "render_relations"))
            self.canvas.update()
        except Exception as e:
            print(e)
    
    def url_changed(self, url: QUrl):
        coords = url.url().split("#map=")[1].split("/")
        lat = float(coords[1])
        lon = float(coords[2])
        self.data = self.osm.data(lon, lat)
        self.canvas.setData(self.data)
        self.canvas.setCamera(lon, lat)
        self.canvas.update()
    
    def editor_visibility_changed(self):
        self.canvas.setEditorVisible(self.editor_menu.isChecked())
        self.canvas.update()

    def export(self):
        export(self.lat, self.lon, 5000, self.osm)
    
    def mousePressEvent(self, event: QMouseEvent):
        self.select_node(event.position().x(), event.position().y())
        self.canvas.update()

    def select_node(self, x, y):
        dis = 1000
        index = -1
        selected_node_index = None
        nodes = self.data["nodes"]
        for node in nodes:
            index += 1
            d = (node.render_x  - x) * (node.render_x  - x) + \
                (node.render_y - y) * (node.render_y - y)
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

