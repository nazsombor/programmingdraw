import xml.sax
from dataclasses import dataclass

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

    def lat(self, lat, scale):
        return (self.lattitude - lat) * scale
    
    def lon(self, lon, scale):
        return (self.longitude - lon) * scale
    
    def is_in_boundary(self, min_lon, min_lat, max_lon, max_lat, lon, lat, scale):
        lo = self.lon(lon, scale)
        la = self.lat(lat, scale)
        return lo > min_lon and lo < max_lon and la > min_lat and la < max_lat

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

@dataclass
class Relation:
    id: int
    tags: list
    members: list
    parent: None
    parent_type: str
    selected: bool
    secondary_selected: bool

    def is_in_boundary(self, min_lon, min_lat, max_lon, max_lat, lon, lat, scale):
        return True

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
    
    def startElement(self, name, attrs):
        match name:
            case "node":
                self.current = "node"
                self.current_node = Node(int(attrs.getValue('id')), [], (float(attrs.getValue('lat'))), (float(attrs.getValue('lon'))), None, None, False, False)
                self.nodes.append(self.current_node)
                
            case "way":
                self.current = "way"
                
                if self.check:
                    self.check = False
                    self.nodes.sort(key=lambda node: node.id)

                self.current_way = Way(int(attrs.getValue('id')), [], [], None, False, None, False, False)
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
            relation = Relation(rel.id, rel.tags, [], None, None, False, False)
            
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
            
            for member in rel.members:
                if member.type == 'relation':
                    relation = search(self.relations, rel.id)
                    r = search(self.relations, member.ref)
                    if r is not None:
                        member = Member(r, mem.type, mem.role)
                        relation.members.append(member)
                        r.parent = relation
                        r.parent_type = "relation"


def osm(file):
    handler = Handler()
    xml.sax.parse(file, handler)        
    return handler.nodes, handler.ways, handler.relations