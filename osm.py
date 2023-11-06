import xml.sax
from dataclasses import dataclass
import math
from threading import Thread

@dataclass
class Node:
    id: int
    tags: list
    lattitude: float
    longitude: float
    parent: None
    parent_type: str
    drawn: bool
    selected: bool
    render_x: float
    render_y: float
    visible: bool

    def lat(self, lat, scale):
        return (self.lattitude - lat) * scale
    
    def lon(self, lon, scale):
        return (self.longitude - lon) * scale

@dataclass
class Way:
    id: int
    tags: list
    nds: list
    parent: None
    parent_type: str
    drawn: bool
    selected: bool
    secondary_selected: bool
    visible: bool

@dataclass
class Relation:
    id: int
    tags: list
    members: list
    parent: None
    parent_type: str
    selected: bool
    secondary_selected: bool
    visible: bool

@dataclass
class Tag:
    k: str
    v: str

@dataclass
class Member:
    member: Node | Way | Relation
    type: str
    role: str

def search(arr, id):
    low = 0
    high = len(arr) - 1
    while low <= high:
        mid = (low + high) // 2
        if arr[mid].id == id:
            return arr[mid]
        else:
            if arr[mid].id < id:
                low = mid + 1
            else:
                high = mid - 1
    return None

class Handler(xml.sax.handler.ContentHandler):
    
    @dataclass
    class RelationFirstRound:
        id: int
        tags: list
        members: list
    
    @dataclass
    class MemberFirstRound:
        type: str
        ref: int
        role: str
    
    current_node = None
    current_way = None
    current_relation = None
    current = None
    
    relations_first_round = []
    
    check = True

    nodes = []
    ways = []
    relations = []

    min_lat = 0
    min_lon = 0
    max_lat = 0
    max_lon = 0
    
    def startElement(self, name, attrs):
        match name:
            case "bounds":
                self.min_lat = float(attrs.getValue('minlat'))
                self.min_lon = float(attrs.getValue('minlon'))
                self.max_lat = float(attrs.getValue('maxlat'))
                self.max_lon = float(attrs.getValue('maxlon'))
            case "node":
                self.current = "node"
                self.current_node = Node(int(attrs.getValue('id')), [], (float(attrs.getValue('lat'))), (float(attrs.getValue('lon'))), None, None, False, False, 0, 0, True)
                self.nodes.append(self.current_node)
                
            case "way":
                self.current = "way"
                
                if self.check:
                    self.check = False
                    self.nodes.sort(key=lambda node: node.id)

                self.current_way = Way(int(attrs.getValue('id')), [], [], None, False, None, False, False, True)
                self.ways.append(self.current_way)
            
            case "relation":
                self.current = "relation"
                self.current_relation = self.RelationFirstRound(int(attrs.getValue('id')), [], [])
                self.relations_first_round.append(self.current_relation)
                
            case "tag":
                tag = Tag(attrs.getValue('k'), attrs.getValue('v'))
                
                match self.current:
                    case "node":self.current_node.tags.append(tag)
                    case "way": self.current_way.tags.append(tag)
                    case "relation": self.current_relation.tags.append(tag)
            
            case "nd":
                node = search(self.nodes, int(attrs.getValue('ref')))
                if node is not None:
                    self.current_way.nds.append(node)
                    node.parent = self.current_way
                    node.parent_type = "way"
                
            case "member":
                member = self.MemberFirstRound(attrs.getValue('type'), int(attrs.getValue('ref')), attrs.getValue('role'))
                self.current_relation.members.append(member)
    
    
    def endDocument(self):
        self.ways.sort(key=lambda way: way.id)
        self.relations_first_round.sort(key=lambda rel: rel.id)
        
        for rel in self.relations_first_round:
            relation = Relation(rel.id, rel.tags, [], None, None, False, False, True)
            
            for mem in rel.members:
                match mem.type:
                    case 'node':
                        node = search(self.nodes, mem.ref)
                        if node is not None:
                            member = Member(node, None, None)
                            relation.members.append(member)
                            node.parent = relation
                            node.parent_type = "relation"
                            
                    case 'way':
                        way = search(self.ways, mem.ref)
                        if way is not None:
                            member = Member(way, mem.type, mem.role)
                            relation.members.append(member)
                            way.parent = relation
                            way.parent_type = "relation"
                            
                    case 'relation':
                        pass
            
            self.relations.append(relation)
            
        for rel in self.relations_first_round:
            for mem in rel.members:
                if mem.type == 'relation':
                    relation = search(self.relations, rel.id)
                    r = search(self.relations, mem.ref)
                    if r is not None:
                        member = Member(r, mem.type, mem.role)
                        relation.members.append(member)
                        r.parent = relation
                        r.parent_type = "relation"

def relation_boundary(relation, min_x, max_x, min_y, max_y, handler, chunk_size_x, chunk_size_y):
    for member in relation.members:
        match member.type:
            case "node":
                y = math.floor((member.member.longitude - handler.min_lon) / (handler.max_lon - handler.min_lon) * chunk_size_y)
                x = math.floor((member.member.lattitude - handler.min_lat) / (handler.max_lat - handler.min_lat) * chunk_size_x)
                if y < min_y:
                    min_y = y
                if y > max_y:
                    max_y = y
                if x < min_x:
                    min_x = x
                if x > max_x:
                    max_x = x
            case "way":
                for node in member.member.nds:
                    y = math.floor((node.longitude - handler.min_lon) / (handler.max_lon - handler.min_lon) * chunk_size_y)
                    x = math.floor((node.lattitude - handler.min_lat) / (handler.max_lat - handler.min_lat) * chunk_size_x)
                    if y < min_y:
                        min_y = y
                    if y > max_y:
                        max_y = y
                    if x < min_x:
                        min_x = x
                    if x > max_x:
                        max_x = x
            case "relation":
                min_x, max_x, min_y, max_y = relation_boundary(member.member, min_x, max_x, min_y, max_y, handler, chunk_size_x, chunk_size_y)
    return min_x, max_x, min_y, max_y

class Osm:

    _data = []
    chunk_size_x: int
    chunk_size_y: int
    min_lon: float
    max_lon: float
    min_lat: float
    max_lat: float

    def __init__(self, file, chunk_size_x, chunk_size_y):
        
        self.chunk_size_x = chunk_size_x
        self.chunk_size_y = chunk_size_y
        
        handler = Handler()
        xml.sax.parse(file, handler)

        self.min_lon = handler.min_lon
        self.max_lon = handler.max_lon
        self.min_lat = handler.min_lat
        self.max_lat = handler.max_lat

        for y in range(self.chunk_size_y):
            row = []
            self._data.append(row)
            for x in range(self.chunk_size_x):
                row.append({
                    "nodes": [],
                    "ways": [],
                    "relations": []
                })
        
        for node in handler.nodes:

            y = math.floor((node.longitude - handler.min_lon) / (handler.max_lon - handler.min_lon) * self.chunk_size_y)
            x = math.floor((node.lattitude - handler.min_lat) / (handler.max_lat - handler.min_lat) * self.chunk_size_x)

            if x < 0: x = 0
            if x > self.chunk_size_x - 1: x = self.chunk_size_x - 1
            if y < 0: y = 0
            if y > self.chunk_size_y - 1: y = self.chunk_size_y - 1

            self._data[y][x]["nodes"].append(node)
        
        for way in handler.ways:

            if len(way.tags) == 0 and node.parent: continue

            min_x = self.chunk_size_x
            max_x = 0
            min_y = self.chunk_size_y
            max_y = 0
            for node in way.nds:
                y = math.floor((node.longitude - handler.min_lon) / (handler.max_lon - handler.min_lon) * self.chunk_size_y)
                x = math.floor((node.lattitude - handler.min_lat) / (handler.max_lat - handler.min_lat) * self.chunk_size_x)       
                if y < min_y:
                    min_y = y
                if y > max_y:
                    max_y = y
                if x < min_x:
                    min_x = x
                if x > max_x:
                    max_x = x
            
            if min_x < 0: min_x = 0
            if max_x > self.chunk_size_x - 1: max_x = self.chunk_size_x - 1
            if min_y < 0: min_y = 0
            if max_y > self.chunk_size_y - 1: max_y = self.chunk_size_y - 1
            
            for y in range(min_y, max_y + 1):
                for x in range(min_x, max_x + 1):
                    self._data[y][x]["ways"].append(way)
        
        for relation in handler.relations:

            if len(relation.tags) == 0 and relation.parent: continue

            min_x = self.chunk_size_x
            max_x = 0
            min_y = self.chunk_size_y
            max_y = 0

            min_x, max_x, min_y, max_y = relation_boundary(relation, min_x, max_x, min_y, max_y, handler, self.chunk_size_x, self.chunk_size_y)

            if min_x < 0: min_x = 0
            if max_x > self.chunk_size_x - 1: max_x = self.chunk_size_x - 1
            if min_y < 0: min_y = 0
            if max_y > self.chunk_size_y - 1: max_y = self.chunk_size_y - 1

            for y in range(min_y, max_y + 1):
                for x in range(min_x, max_x + 1):
                    self._data[y][x]["relations"].append(relation)

    def data(self, lon, lat):
        y = math.floor((lon - self.min_lon) / (self.max_lon - self.min_lon) * self.chunk_size_y)
        x = math.floor((lat - self.min_lat) / (self.max_lat - self.min_lat) * self.chunk_size_x)
        if y < 1: y = 1
        if y > self.chunk_size_y - 2: y = self.chunk_size_y - 2
        if x < 1: x = 1
        if x > self.chunk_size_x - 2: x = self.chunk_size_x - 2

        d = {
            "nodes": [],
            "ways": [],
            "relations": []
        }

        threads = []

        for i in range(y-1, y+2):
            for j in range(x-1, x+2):
                thread = Thread(target=append, args=(d["nodes"], self._data[i][j]["nodes"]))
                threads.append(thread)
                thread.start()
                thread = Thread(target=append, args=(d["ways"], self._data[i][j]["ways"]))
                threads.append(thread)
                thread.start()
                thread = Thread(target=append, args=(d["relations"], self._data[i][j]["relations"]))
                threads.append(thread)
                thread.start()
        
        for thread in threads:
            thread.join()

        return d

def append(target, source):
    for s in source:
        target.append(s)