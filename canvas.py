from PySide6.QtGui import QPaintEvent, QPainter
from PySide6.QtCore import Qt
from PySide6.QtOpenGLWidgets import QOpenGLWidget
from threading import Thread


class Canvas(QOpenGLWidget):

    visible = False

    def setEditorVisible(self, visible):
        self.visible = visible

    def setData(self, nodes, ways, relations):
        self.nodes = nodes
        self.ways = ways
        self.relations = relations
    
    def setCamera(self, longitude, lattitude, scale):
        self.longitude = longitude
        self.lattitude = lattitude
        self.scale = scale
        self.threaded_update_location(self.nodes, self.update_nodes_location, 1)
        self.threaded_update_location(self.ways, self.update_ways_location, 1)
        self.threaded_update_location(self.relations, self.update_relations_location, 1)

    def setRender(self, render_nodes, render_ways, render_relations):
        self.render_nodes = render_nodes
        self.render_ways = render_ways
        self.render_relations = render_relations

    def paintEvent(self, event: QPaintEvent) -> None:
        painter = QPainter()
        painter.begin(self)
        painter.fillRect(event.rect(), Qt.GlobalColor.white)
        self.render_nodes(painter, self.nodes, self.visible)
        self.render_relations(painter, self.relations, self.visible)
        self.render_ways(painter, self.ways, self.visible)
        painter.end()

    def update_nodes_location(self, nodes, start, end):
        for node in nodes[start:end]:
            node.render_x = node.lon(self.longitude, self.scale)
            node.render_y = node.lat(self.lattitude, self.scale)
    
    def update_ways_location(self, ways, start, end):
        for way in ways[start:end]:
            self.update_nodes_location(way.nds, 0, len(way.nds))
    
    def update_relations_location(self, relations, start, end):
        for relation in relations[start:end]:
            member_nodes = []
            for member in relation.members:
                match member.type:
                    case "node": member_nodes.append(member.member)
                    case "way": self.update_nodes_location(member.member.nds, 0, len(member.member.nds))
            self.update_nodes_location(member_nodes, 0, len(member_nodes))

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