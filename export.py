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

def nodes_to_coords(nodes):
    list = []
    for node in nodes:
        list.append((node.lattitude, node.longitude))

def export(lat, lon, scale, nodes, ways, relations):

    data = []

    for way in ways:

        if has_parent_but_no_tag(way): continue

        if has_tag(way.tags, "building"):
            data.append({
                "object_type": "building",
                "outline": nodes_to_coords(way.nds),
                "holes": [],
                "levels": int(tag_value(way.tags, "levels", 1))
            })

        elif has_tag(way.tags, "highway"):
            data.append({
                "object_type": "highway",
                "type": tag_value(way.tags, "highway"),
                "path": nodes_to_coords(way.nds)
            })

        elif has_tag(way.tags, "natural", "tree_group"):
            data.append({
                "object_type": "tree_group",
                "outline": nodes_to_coords(way.nds),
                "holes": []
            })

        elif has_tag(way.tags, "barrier", "fence"):
            data.append({
                "object_type": "fence",
                "path":  nodes_to_coords(way.nds)
            })
    
    for relation in relations:
        outline = None
        holes = []
        agregated = []
        for member in relation.members:
            if member.type == "way":
                if member.role == "outer":
                    outline = nodes_to_coords(member.member.nds)
                elif member.role == "inner":
                    holes.append(nodes_to_coords(member.member.nds))
                for node in member.member.nds:
                    agregated.append((node.lattitude, node.longitude))
        
        if has_tag(relation.tags, "building"):
            data.append({
                "object_type": "building",
                "outline": outline,
                "holes": holes,
                "levels": int(tag_value(relation.tags, "levels", 1))
            })

        if has_tag(relation.tags, "water", "river"):
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