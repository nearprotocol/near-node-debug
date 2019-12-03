template = """
Me: {me}

Nodes:
{nodes}

Edges:
{edges}
"""

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
        "edges" : [
            f"{peer0}, {peer1} = {value}" for ((peer0, peer1), value) in glob_edges.items()
        ]
    }
