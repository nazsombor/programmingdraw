import pickle
import os

def has_tag(tags, k, v=None):
    for tag in tags:
        if k in tag.k:
            if v == None:
                return True
            elif v in tag.v:
                return True
    return False

def tag_value(tags, k, default=None):
    for tag in tags:
        if k in tag.k:
            return tag.v
    return default

def has_parent_but_no_tag(way):
    return way.parent and len(way.tags) == 0

def export(lat, lon, scale, nodes, ways, relations):

    data = []

    for way in ways:

        if has_parent_but_no_tag(way): continue

        x = 0
        y = 0
        path = []

        for node in way.nds:
            x += node.lat * scale
            y += node.lon * scale

        x /= len(way.nds)
        y /= len(way.nds)

        for node in way.nds:
            path.append((node.lat * scale - x, node.lon * scale - y))

        if has_tag(way.tags, "building"):
            data.append({
                "object_type": "building",
                "outline": path,
                "holes": [],
                "levels": int(tag_value(way.tags, "levels", 1))
            })

        elif has_tag(way.tags, "highway"):
            data.append({
                "object_type": "highway",
                "type": tag_value(way.tags, "highway"),
                "path": path
            })

        elif has_tag(way.tags, "natural", "tree_group"):
            data.append({
                "object_type": "tree_group",
                "outline": path,
                "holes": []
            })

        elif has_tag(way.tags, "barrier", "fence"):
            data.append({
                "object_type": "fence",
                "path":  path
            })
    
    for relation in relations:
        x = 0
        y = 0
        path = []
        holes = []
        agregated = []
        
        if has_tag(relation.tags, "building"):
            for member in relation.members:
                if member.role == "outer":
                    for node in member.member.nds:
                        x += node.lat * scale
                        y += node.lon * scale
                    
                    x /= len(member.member.nds)
                    y /= len(member.member.nds)

                    for node in member.member.nds:
                        path.append((node.lat * scale - x, node.lon * scale - y))
                
                if member.role == "inner":
                    hole = []
                    holes.append(hole)
                    for node in member.member.nds:
                        hole.append((node.lat * scale - x, node.lon * scale - y))

            data.append({
                "object_type": "building",
                "outline": path,
                "holes": holes,
                "levels": int(tag_value(relation.tags, "levels", 1))
            })

        if has_tag(relation.tags, "water", "river"):
            for member in relation.members:
                for node in member.member.nds:
                    agregated.append((node.lat * scale - x, node.lon * scale - y))

            data.append({
                "object_type": "river",
                "outline": agregated
            })
            
    try:
        os.remove("map.pickle")
    except:
        pass
    with open("map.pickle", "wb") as file:
        pickle.dump(data, file)