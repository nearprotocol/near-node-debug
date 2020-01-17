import math
import time
from random import randint, random
from threading import Thread

import networkx as nx
import numpy as np
import requests


class Fetcher(Thread):
    def __init__(self, bootstrap, callback):
        self._all_nodes = [bootstrap]
        self._callback = callback
        super().__init__()

    def run(self):
        while True:
            new_node = False

            for node in list(self._all_nodes):
                res = requests.get(node + "/network_info").json()

                self._callback(node, res)

                # Populate all nodes
                for peer in res['active_peers']:
                    ip, port = peer['addr'].split(':')
                    if ip == '127.0.0.1':
                        port = 3030 + int(port) - 24567
                    else:
                        port = 3030
                    addr = f"http://{ip}:{port}"

                    if addr not in self._all_nodes:
                        self._all_nodes.append(addr)
                        new_node = True

            if not new_node:
                time.sleep(5)


class Api:
    def __init__(self, bootstrap):
        self.fetcher = Fetcher(bootstrap, self.handle)
        self.fetcher.start()
        self.nodes = {}

    def handle(self, node_url, info):
        me = info['metric_recorder']['me']
        self.nodes[me] = info

    def num_nodes(self):
        return len(self.nodes)

    def diameter(self):
        return nx.diameter(self.get_graph())

    def node_ix(self):
        return {node_id: ix for (
            ix, node_id) in enumerate(sorted(self.nodes))}

    def get_graph(self):
        G = nx.Graph()
        n = self.num_nodes()

        for u in range(n):
            G.add_node(u)
            G.nodes[u]['pos'] = (math.cos(u / n * 2 * math.pi),
                                 math.sin(u / n * 2 * math.pi))

        node_ix = self.node_ix()

        if len(self.nodes):
            graph = next(iter(self.nodes.items()))[
                1]['metric_recorder']['graph']
            for (u, v) in graph:
                u = node_ix[u]
                v = node_ix[v]
                G.add_edge(u, v)

        return G

    def get_latency_heatmap(self):
        n = self.num_nodes()
        node_ix = self.node_ix()

        lat = np.zeros((n, n))
        t = float('inf')

        for u, data in self.nodes.items():
            u = node_ix.get(u)
            for (v, l) in data['metric_recorder']['latencies'].items():
                v = node_ix.get(v, -1)
                if v == -1:
                    continue
                lat[u][v] = l['mean_latency']
                t = min(t, lat[u][v])

        for i in range(n):
            lat[i][i] = t

        return lat

    def get_transfer_bytes_heatmap(self):
        n = self.num_nodes()
        node_ix = self.node_ix()

        res = np.zeros((n, n))
        t = float('inf')

        for u, data in self.nodes.items():
            u = node_ix.get(u)
            for (v, l) in data['metric_recorder']['per_peer'].items():
                v = node_ix.get(v, -1)
                if v == -1:
                    continue
                res[u][v] = l['received']['bytes']
                t = min(t, res[u][v])

        for i in range(n):
            res[i][i] = t

        return res

    def get_transfer_count_heatmap(self):
        n = self.num_nodes()
        node_ix = self.node_ix()

        res = np.zeros((n, n))
        t = float('inf')

        for u, data in self.nodes.items():
            u = node_ix.get(u)
            for (v, l) in data['metric_recorder']['per_peer'].items():
                v = node_ix.get(v, -1)
                if v == -1:
                    continue
                res[u][v] = l['received']['count']
                t = min(t, res[u][v])

        for i in range(n):
            res[i][i] = t

        return res

    def get_received_type(self):
        size, total, labels = [], [], []
        for (label, data) in next(iter(self.nodes.items()))[1]['metric_recorder']['per_type'].items():
            labels.append(label)
            size.append(data['received']['bytes'])
            total.append(data['received']['count'])
        return size, total, labels

    def get_received_peer(self):
        size, total, labels = [], [], []
        for (label, data) in next(iter(self.nodes.items()))[1]['metric_recorder']['per_peer'].items():
            labels.append(label)
            size.append(data['received']['bytes'])
            total.append(data['received']['count'])
        return size, total, labels

    def summary(self):
        g = self.get_graph()
        header = ["Node ID", "Active peers"]
        values = [[], []]

        for u, node_id in enumerate(self.nodes):
            values[0].append(node_id)
            values[1].append(len(g[u]))

        return header, values
