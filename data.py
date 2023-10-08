selectable_nodes = []

def has_tag(tags, k, v):
    for tag in tags:
        if k == tag.k and v == tag.v:
            return True
    return False

def filter_nodes(nodes):
    global selectable_nodes
    selectable_nodes = []

    list = []

    for node in nodes:
        if not node.parent:
            list.append(node)
            selectable_nodes.append(node)

    return list

def filter_ways(ways):
    list = []
    for way in ways:
        if way.parent: continue

        list.append(way)
        for node in way.nds:
            selectable_nodes.append(node)
    return list

def filter_relations(relations):
    list = []
    for relation in relations:
        
        if has_tag(relation.tags, "boundary", "religious_administration"):
            continue
        
        if has_tag(relation.tags, "route", "subway"):
            continue

        if has_tag(relation.tags, "route", "tram"):
            continue

        if has_tag(relation.tags, "route", "bus"):
            continue

        list.append(relation)
        for member in relation.members:
            if member.type == "node":
                selectable_nodes.append(member.member)
            elif member.type == "way":
                for node in member.member.nds:
                    selectable_nodes.append(node)

    return list