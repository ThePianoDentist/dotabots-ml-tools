from elasticsearch import Elasticsearch


class DBConnection:
    def __init__(self):
        self.db = Elasticsearch([{'host': 'localhost', 'port': 9200}])

    def get_run(self, task, id):
        result = self.db.get(index=task, doc_type="run", id=id)
        if result["found"]:
            return result["_source"]
        else:
            raise Exception("Could not find result id: %s in database" % id)   #TODO how do I want to handle this?