from PySide6.QtGui import QPaintEvent, QPainter
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget
from threading import Thread


class Canvas(QWidget):

    visible = False
    scale = 5000 * 17

    def setEditorVisible(self, visible):
        self.visible = visible

    def setData(self, data):
        self.nodes = data["nodes"]
        self.ways = data["ways"]
        self.relations = data["relations"]
    
    def setCamera(self, longitude, lattitude):
        self.longitude = longitude
        self.lattitude = lattitude
        self.threaded_update_location(self.nodes, self.update_nodes_location, 9)
        self.threaded_update_location(self.ways, self.update_ways_location, 9)
        self.threaded_update_location(self.relations, self.update_relations_location, 9)

    def setRender(self, render_nodes, render_ways, render_relations):
        self.render_nodes = render_nodes
        self.render_ways = render_ways
        self.render_relations = render_relations

    def paintEvent(self, event: QPaintEvent) -> None:
        painter = QPainter()
        painter.begin(self)
        self.render_nodes(painter, self.nodes, self.visible)
        self.render_ways(painter, self.ways, self.visible)
        self.render_relations(painter, self.relations, self.visible)
        painter.end()

    def update_nodes_location(self, nodes, start, end):
        for node in nodes[start:end]:
            node.render_x = node.lon(self.longitude, self.scale) + self.rect().width() / 2
            node.render_y = -node.lat(self.lattitude, self.scale) + self.rect().height() / 2
    
    def update_ways_location(self, ways, start, end):
        for way in ways[start:end]:
            for node in way.nds:
                node.render_x = node.lon(self.longitude, self.scale) + self.rect().width() / 2
                node.render_y = -node.lat(self.lattitude, self.scale) + self.rect().height() / 2
    
    def update_relations_location(self, relations, start, end):
        for relation in relations[start:end]:
            for member in relation.members:
                match member.type:
                    case "node":
                        node = member.member
                        node.render_x = node.lon(self.longitude, self.scale) + self.rect().width() / 2
                        node.render_y = -node.lat(self.lattitude, self.scale) + self.rect().width() / 2
                    case "way":
                        for node in member.member.nds:
                            node.render_x = node.lon(self.longitude, self.scale) + self.rect().width() / 2
                            node.render_y = -node.lat(self.lattitude, self.scale) + self.rect().height() / 2

    def threaded_update_location(self, items, function, thread_num):
        length = len(items)
        split_size = length // thread_num
        threads = []

        for i in range(thread_num):                                                 
            start = i * split_size                                                  
            end = None if i+1 == thread_num else (i+1) * split_size                 
            threads.append(Thread(target=function, args=(items, start, end)))         
            threads[-1].start()

        for t in threads:                                                           
            t.join()  