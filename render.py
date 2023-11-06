from PySide6.QtGui import *
from PySide6.QtCore import *

building_color = QColor(215, 208, 202, 255)
building_outline_color = QColor(200, 190, 182, 255)
highway_color = QColor(200, 200, 200, 255)
tree_group_color = QColor(180, 208, 163, 255)
park_color = QColor(210, 249, 208, 255)
river_color = QColor(178, 210, 221, 255)

def nodes_to_path(nodes):
    path = QPainterPath()
    path.moveTo(nodes[0].render_x, nodes[0].render_y)
    for i in range(1, len(nodes)):
        path.lineTo(nodes[i].render_x, nodes[i].render_y)
    return path

def render_nodes(painter: QPainter, nodes, visible):
    pen = QPen()

    for node in nodes:
        if node.selected:
            pen.setColor(Qt.GlobalColor.red)
            pen.setWidth(5)
        else:
            pen.setColor(Qt.GlobalColor.black)
            pen.setWidth(2)

        painter.setPen(pen)
        painter.drawPoint(QPointF(node.render_x, node.render_y))

def render_ways(painter: QPainter, ways, visible):
    pen = QPen()

    for way in ways:
        path = nodes_to_path(way.nds)
        for tag in way.tags:
            if "building" in tag.k:
                painter.fillPath(path, building_color)
                pen.setColor(building_outline_color)
                pen.setWidth(1)
                painter.setPen(pen)
                painter.drawPath(path)
            elif "highway" == tag.k:
                pen.setColor(highway_color)
                pen.setWidth(5)
                painter.setPen(pen)
                painter.drawPath(path)
            elif "natural" == tag.k and "tree_group" == tag.v:
                painter.fillPath(path, tree_group_color)
            elif "leisure" == tag.k and "park" == tag.v:
                painter.fillPath(path, park_color)

        if way.selected:
            pen.setColor(Qt.GlobalColor.red)
            pen.setWidth(2)
            print("====== SELECTED ========")
        else:
            pen.setColor(Qt.GlobalColor.black)
            pen.setWidth(1)

        painter.setPen(pen)
        painter.drawPath(path)
    
def render_relations(painter: QPainter, relations, editor_visible):
    pen = QPen()

    for relation in relations:
        for member in relation.members:
            match member.type:
                case "way":
                    if member.member.selected:
                        pen.setColor(Qt.GlobalColor.red)
                        pen.setWidth(2)
                    elif member.member.secondary_selected:
                        pen.setColor(Qt.GlobalColor.green)
                        pen.setWidth(2)
                    else:
                        pen.setColor(Qt.GlobalColor.black)
                        pen.setWidth(1)
                    path = nodes_to_path(member.member.nds)
                    painter.setPen(pen)
                    painter.drawPath(path)
