from PyQt6 import QtGui, QtCore
from PyQt6.QtCore import *

def nodes_to_path(nodes, lat, lon, scale):
    path = QtGui.QPainterPath()
    path.moveTo(nodes[0].lon(lon, scale), -nodes[0].lat(lat, scale))
    for i in range(1, len(nodes)):
        path.lineTo(nodes[i].lon(lon, scale), -nodes[i].lat(lat, scale))
    return path

def way_has_tag(way, k="", v=""):
    for tag in way.tags:
        if k == tag.k and tag.v == v:
            return True    
    return False
                
def parent_has_tag(way, k="", v=""):
    if not way.parent:
        return False
    for tag in way.parent.tags:
        if k == tag.k and v == tag.v:
            return True
    return False

def is_node_visible(node, lon, lat, scale):
    return True
    if node.parent and node.parent_type == "relation":
        return is_relation_visible(node.parent, lon, lat, scale)
    return is_node_visible_from_height(node, scale) and node.is_in_boundary(0, 0, 1728, 965, lon, lat, scale)
    
def is_way_visible(way, lon, lat, scale):
    return True
    if way.parent:
        return self.is_relation_visible(way.parent)
    return way.is_visible_from_height(self.scale) and way.is_in_boundary(0, 0, 1728, 965, self.lon, self.lat, self.scale)

def is_relation_visible(relation, lon, lat, scale):
    if relation.parent:
        return is_relation_visible(relation.parent, lon, lat, scale)
    return is_relation_visible_from_height(relation, scale) and relation.is_in_boundary(0, 0, 1728, 965, lon, lat, scale)

def is_node_visible_from_height(node, scale):
    return True

def is_relation_visible_from_height(node, scale):
    return True

def render_nodes(painter: QtGui.QPainter, nodes, lon, lat, scale):
    pen = QtGui.QPen()

    for node in nodes:
        if not is_node_visible(node, lon, lat, scale): continue

        if node.selected:
            pen.setColor(Qt.GlobalColor.red)
            pen.setWidth(5)
            painter.setPen(pen)
        else:
            pen.setColor(Qt.GlobalColor.black)
            pen.setWidth(2)
            painter.setPen(pen)

        painter.drawPoint(QtCore.QPointF(node.lon(lon, scale), -node.lat(lat, scale)))

def render_ways(painter, ways, lon, lat, scale):
    pen = QtGui.QPen()

    for way in ways:
        if not is_way_visible(way, lon, lat, scale): continue
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

        painter.drawPath(nodes_to_path(way.nds, lat, lon, scale))
    
def render_relations(painter, relations, lon, lat, scale):
    pen = QtGui.QPen()

    for relation in relations:
        if not is_relation_visible(relation, lon, lat, scale): continue
        member_nodes = []
        for member in relation.members:
            if member.type == "node":
                member_nodes.append(member.member)
        if len(member_nodes) > 2:
            painter.drawPath(nodes_to_path(member_nodes, lat, lon, scale))
