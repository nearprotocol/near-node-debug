def key_from_message(msg):
    if isinstance(msg, str):
        return msg
    elif isinstance(msg, dict):
        return list(msg.keys())[0]
    else:
        print("Message skip:", msg)

def all_message_types(collection):
    all_types = set()

    for message in collection.find({}):
        key = key_from_message(message['message'])

        if not key in all_types:
            all_types.add(key)
            print(key)

            if key == 'LastEdge':
                print(message)

    return all_types