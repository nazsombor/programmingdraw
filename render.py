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
    path.moveTo(nodes[0].render_x, -nodes[0].render_y)
    for i in range(1, len(nodes)):
        path.lineTo(nodes[i].render_x, -nodes[i].render_y)
    return path

def render_nodes(painter: QPainter, nodes, editor_visible):
    pen = QPen()

    if not editor_visible: return

    for node in nodes:
        if node.selected:
            pen.setColor(Qt.GlobalColor.red)
            pen.setWidth(5)
            painter.setPen(pen)
        else:
            pen.setColor(Qt.GlobalColor.black)
            pen.setWidth(2)
            painter.setPen(pen)

        painter.drawPoint(QPointF(node.render_x, -node.render_y))

def render_ways(painter: QPainter, ways, editor_visible):
    pen = QPen()

    for way in ways:
        render_nodes(painter, way.nds, editor_visible)
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

        if not editor_visible: continue

        if way.selected:
            pen.setColor(Qt.GlobalColor.red)
            pen.setWidth(2)
            painter.setPen(pen)
        elif way.secondary_selected:
            pen.setColor(Qt.GlobalColor.green)
            pen.setWidth(2)
            painter.setPen(pen)
        else:
            pen.setColor(Qt.GlobalColor.black)
            pen.setWidth(1)
            painter.setPen(pen)
        painter.drawPath(path)
    
def render_relations(painter: QPainter, relations, editor_visible):
    pen = QPen()

    for relation in relations:
        member_nodes = []
        member_ways = []
        outer_line = None
        holes = []
        for member in relation.members:
            if member.type == "node":
                member_nodes.append(member.member)
            if member.type == "way":
                member_ways.append(member.member)
                if member.role == "outer":
                    outer_line = nodes_to_path(member.member.nds)
                if member.role == "inner":
                    holes.append(nodes_to_path(member.member.nds))
        
        if editor_visible:
            if len(member_nodes) > 2:
                painter.drawPath(nodes_to_path(member_nodes))
            #todo: draw member ways


        for tag in relation.tags:
            if "building" in tag.k:
                painter.fillPath(outer_line, building_color)
                pen.setColor(building_outline_color)
                pen.setWidth(1)
                painter.setPen(pen)
                painter.drawPath(outer_line)
                for hole in holes:
                    painter.fillPath(hole, Qt.GlobalColor.white)

                    painter.drawPath(hole)
            elif "water" == tag.k and "river" == tag.v:
                boundary = []
                for way in member_ways:
                    for node in way.nds:
                        boundary.append(node)
                painter.fillPath(nodes_to_path(boundary), river_color)
            elif "leisure" == tag.k and "park" == tag.v:
                painter.fillPath(outer_line, park_color)



        render_ways(painter, member_ways, editor_visible)

