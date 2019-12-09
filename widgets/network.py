import networkx as nx

def get_network(collection):
    cursor = collection.find({"message.Sync" : {"$exists" : True}})

    me = None
    nodes = set()
    glob_edges = {}

    for message in cursor:
        me = message['me']
        edges = message['message']['Sync']['edges']

        for edge in edges:
            peer0 = edge['peer0']
            peer1 = edge['peer1']
            nonce = edge['nonce']

            nodes.add(peer0)
            nodes.add(peer1)

            cur_nonce = glob_edges.get((peer0, peer1), 0)
            nonce = int(nonce)

            if nonce > cur_nonce:
                glob_edges[(peer0, peer1)] = nonce

    return {
        "me" : me,
        "nodes" : nodes,
        "edges" : glob_edges,
    }


def get_network_graph(collection):
    context = get_network(collection)

    me = context['me']

    nodes = [{
        'id' : node,
        'label' : node,
        'size' : 1,
        'x' : 0,
        'y' : 0,
        'color' : '#000' if node != me else '#FF0'
    } for node in context['nodes']]

    edges = [{
        "id" : peer0 + peer1,
        "label" : value,
        "source" : peer0,
        "target" : peer1,
        "color" : "#0F0" if value % 2 == 1 else "#F00"
    } for ((peer0, peer1), value) in context['edges'].items()]

    graph = nx.Graph()

    for node in nodes:
        graph.add_node(node['id'])

    for edge in edges:
        graph.add_edge(edge['source'], edge['target'])

    layout = nx.kamada_kawai_layout(graph)

    for node in nodes:
        x, y = layout[node['id']]
        node['x'] = x
        node['y'] = y

    return {
        "nodes" : nodes,
        "edges" : edges,
    }