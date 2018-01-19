import pickle


def load_alias_map(filename):
    with open(filename, "rb") as f:
        unpickler = pickle.Unpickler(f)
        alias_map = unpickler.load()
    return alias_map


def get_alias_ids(_map, uid):
    # TODO aliases = [key for key in _map.keys() if _map[key] == uid and key != uid]
    aliases = set()
    if _map[uid] != uid:
        aliases.add(_map[uid])
    for key in _map.keys():
        if _map[key] == uid and key != uid:
            aliases.add(key)
    return list(aliases)


def find_uid(_map, aliases):
    uid = None
    for a in aliases:
        if a in _map.values():
            uid = a
            break
    return uid
