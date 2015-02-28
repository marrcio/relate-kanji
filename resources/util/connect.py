from pymongo import MongoClient
import uri
client = None

def get_db(db_name):
    global client = MongoClient(uri.uri)
    return client[db_name]

def close():
    client.close() if client is not None
