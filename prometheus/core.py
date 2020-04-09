import math
import time
from random import randint, random
from threading import Thread

import networkx as nx
import numpy as np
import requests

NETWORK_INFO = 'network_info'
STATUS = 'status'
SLEEP_TIME = 5


class Fetcher(Thread):
    def __init__(self, bootstrap, data_callback):
        self._all_nodes = [bootstrap]
        self._callback = data_callback
        super().__init__()

    def populate(self, active_peers):
        new_node = False
        for peer in active_peers:
            ip, port = peer['addr'].split(':')
            if ip == '127.0.0.1':
                port = 3030 + int(port) - 24567
            else:
                port = 3030
            addr = f"http://{ip}:{port}"

            if addr not in self._all_nodes:
                self._all_nodes.append(addr)
                new_node = True
        return new_node

    def run(self):
        while True:
            new_node = False

            for node in list(self._all_nodes):
                # Fetch all data
                res_network_info = requests.get(
                    node + "/" + NETWORK_INFO).json()
                me = res_network_info['metric_recorder']['me']
                res_status = requests.get(node + "/" + STATUS).json()

                # Build dictionary with all data and execute callback
                info = {
                    NETWORK_INFO: res_network_info,
                    STATUS: res_status
                }
                self._callback(me, info)

                # Populate all nodes
                new_node |= self.populate(
                    active_peers=res_network_info['active_peers'])

            if not new_node:
                time.sleep(SLEEP_TIME)


class Api:
    def __init__(self, bootstrap, handle_callback):
        self._handle_callback = handle_callback
        self.fetcher = Fetcher(bootstrap, self.handle)
        self.fetcher.start()
        self.nodes = {}

    def heights(self):
        answer = []
        for _, node in self.nodes.items():
            answer.append(node[STATUS]['sync_info']['latest_block_height'])
        return answer

    def stats_per_type_of_message(self):
        data = {}
        for _, node in self.nodes.items():
            for key, value in node[NETWORK_INFO]['metric_recorder']['per_type'].items():
                if not key in data:
                    # Sent count sum / Sent count max / Sent bytes sum / Sent bytes max
                    data[key] = [0, 0, 0, 0]
                count = value['sent']['count']
                size = value['sent']['bytes']

                data[key][0] += count
                data[key][1] = max(data[key][1], count)
                data[key][2] += size
                data[key][3] = max(data[key][3], size)
        return data

    def validators(self):
        if len(self.nodes) == 0:
            return 0
        _, node = next(iter(self.nodes.items()))
        return len(node[STATUS]['validators'])

    def handle(self, me, info):
        self.nodes[me] = info
        self._handle_callback(self, me)

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
            for (v, l) in data[NETWORK_INFO]['metric_recorder']['latencies'].items():
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
            for (v, l) in data[NETWORK_INFO]['metric_recorder']['per_peer'].items():
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
            for (v, l) in data[NETWORK_INFO]['metric_recorder']['per_peer'].items():
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
            size.append(data[NETWORK_INFO]['received']['bytes'])
            total.append(data[NETWORK_INFO]['received']['count'])
        return size, total, labels

    def get_received_peer(self):
        size, total, labels = [], [], []
        for (label, data) in next(iter(self.nodes.items()))[1]['metric_recorder']['per_peer'].items():
            labels.append(label)
            size.append(data[NETWORK_INFO]['received']['bytes'])
            total.append(data[NETWORK_INFO]['received']['count'])
        return size, total, labels

    def summary(self):
        g = self.get_graph()
        header = ["Node ID", "Active peers"]
        values = [[], []]

        for u, node_id in enumerate(self.nodes):
            values[0].append(node_id)
            values[1].append(len(g[u]))

        return header, values
