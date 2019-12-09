from flask import Flask, request, jsonify
from flask import render_template
from pymongo import MongoClient
from json import dumps
from copy import deepcopy

from widgets.debug import all_message_types
from widgets.network import get_network, get_network_graph


app = Flask(__name__)

collection = None

# MongoDB don't accept numbers greater signed 64 bits integer (2**63 - 1).
# Convert such numbers into strings.
def fix(value):
    # TODO: Convert to  time
    try:
        value = int(value)
        if value >= 2**63:
            value = str(value)
        return value
    except:
        pass

    if isinstance(value, str):
        return value

    if isinstance(value, dict):
        new_dic = {}
        for key, value in value.items():
            if key == '_id':
                continue
            new_dic[key] = fix(value)
        return new_dic

    if isinstance(value, list):
        new_list = [fix(x) for x in value]
        return new_list

    if value is None:
        return value

    assert False, f"{str(value)} | {type(value)}"


@app.route('/', methods=['POST'])
def hello():
    print("Received message")
    data = request.json
    data = fix(data)
    tmp_data = deepcopy(data)
    try:
        collection.insert_one(data)
        print("Inserted")
    except:
        print("\nERROR")
        print(dumps(tmp_data))
    return ''


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/data')
def all_data():
    cursor = collection.find({})
    data = list(reversed([dumps(fix(x)) for x in cursor]))
    print("GET:", len(data))
    context={'data' : data}
    return render_template('data.html', **context)


@app.route('/edges')
def edges():
    cursor = collection.find({"$or": [{"message.Sync" : {"$exists" : True}}, {"message.Handshake" : {"$exists" : True}}]})
    data = [x for x in cursor]
    context = {'data' : data}
    return render_template('data.html', **context)


@app.route('/message_types')
def debug():
    return str(all_message_types(collection))


@app.route('/api/network')
def api_network():
    return jsonify(get_network_graph(collection))


@app.route('/network')
def network():
    return render_template('network.html')


def start_server(port, debug, database_name, database_addr):
    global collection

    db_ip, db_port = database_addr.split(':')
    client = MongoClient(db_ip, int(db_port))
    db = client[database_name]
    collection =  db['info']

    app.run('0.0.0.0', port=port, debug=debug)


if __name__ == '__main__':
    start_server(8181, True, 'second', 'localhost:27017')
