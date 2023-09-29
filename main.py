import typing
from PyQt6 import QtGui
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
import sys
import importlib
from project.osm import osm
import threading

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setFixedWidth(1728)
        self.setFixedHeight(965)

        projectWatcher = QFileSystemWatcher(self)
        projectWatcher.addPath("/Users/anagy/Projects/programmingdraw/project/render.py")
        projectWatcher.fileChanged.connect(self.file_changed)
    
        self.label = QLabel()
        canvas = QPixmap(1728, 965)
        canvas.fill(Qt.GlobalColor.white)
        self.label.setPixmap(canvas)
        self.setCentralWidget(self.label)

        self.module = importlib.import_module("project.render")

        self.nodes, self.ways, self.relations = osm("project/hungary-latest.osm")
        self.zoom, self.lat, self.lon = 17, 47.49001, 19.05665 #at 17th zoom, the correction should be: 47.49610, 19.04914
        self.scale = 5000 * self.zoom
        self.lat -= -0.00609
        self.lon -= 0.00751

        self.selected_node = None

        self.render()

    def file_changed(self, path):
        try:
            importlib.reload(self.module)
            print("module is successfully reloaded")
            self.render()
        except Exception as e:
            print(e)
    
    def render(self):
        canvas = self.label.pixmap()
        painter = QPainter(canvas)
        
        canvas.fill(Qt.GlobalColor.white)

        self.threaded_render(painter, self.ways, "render_ways", 200)
        self.threaded_render(painter, self.relations, "render_relations", 200)
        self.threaded_render(painter, self.nodes, "render_nodes", 200)
        
        painter.end()
        self.label.setPixmap(canvas)
    
    def threaded_render(self, painter, items, function_name, thread_num):
        length = len(items)
        split_size = length // thread_num
        threads = []

        for i in range(thread_num):                                                 
            start = i * split_size                                                  
            end = None if i+1 == thread_num else (i+1) * split_size                 
            threads.append(threading.Thread(target=getattr(self.module, function_name), args=(painter, items[start:end], self.lon, self.lat, self.scale)))         
            threads[-1].start()

        for t in threads:                                                           
            t.join()   

    def mousePressEvent(self, event: QMouseEvent):
        self.last_mouse_position_x = event.pos().x()
        self.last_mouse_position_y = event.pos().y()

        self.select_node(event.pos().x(), event.pos().y())

    def mouseMoveEvent(self, event: QMouseEvent):
        self.delta_mouse_position_x = event.pos().x() - self.last_mouse_position_x
        self.delta_mouse_position_y = event.pos().y() - self.last_mouse_position_y

        self.lon += -self.delta_mouse_position_x / self.scale
        self.lat += self.delta_mouse_position_y / self.scale

        self.last_mouse_position_x = event.pos().x()
        self.last_mouse_position_y = event.pos().y()

        self.render()
    
    def wheelEvent(self, event: QWheelEvent) -> None:
        self.scale += event.angleDelta().y() * 2
        self.render()

    def select_node(self, x, y):
        dis = 10000000
        index = -1
        selected_node_index = None
        for node in self.nodes:
            index += 1
            d = (node.lon(self.lon, self.scale)  - x) * (node.lon(self.lon, self.scale)  - x) + \
                (-node.lat(self.lat, self.scale) - y) * (-node.lat(self.lat, self.scale) - y)
            if dis > d:
                dis = d
                selected_node_index = index

        if selected_node_index:
            if self.selected_node:
                self.selected_node.selected = False
                self.select_parent(self.selected_node, False)
            self.selected_node = self.nodes[selected_node_index]
            self.selected_node.selected = True
            self.select_parent(self.selected_node, True)
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

app = QApplication(sys.argv)

window = MainWindow()
window.show()

app.exec()

