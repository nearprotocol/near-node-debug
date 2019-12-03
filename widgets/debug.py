def all_message_types(collection):
    all_types = set()

    for message in collection.find({}):
        key = list(message['message'].keys())[0]

        if not key in all_types:
            all_types.add(key)
            print(key)

            if key == 'LastEdge':
                print(message)

    return all_types