import logging
from elasticsearch import Elasticsearch

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DBConnection:
    def __init__(self, task, net_id):
        self.db = Elasticsearch([{'host': 'localhost', 'port': 80}])
        self.task = task
        self.net_id = net_id

    def get_run(self, id):
        logger.info("Getting run %s from database" % id)
        result = self.db.get(index=self.task, doc_type="run%s" % self.net_id, id=id)
        if result["found"]:
            return result["_source"]
        else:
            raise Exception("Could not find result id: %s in database" % id)   #TODO how do I want to handle this?

    def add_run(self, id, data):
        logger.info("Adding run %s to database" % id)
        logger.debug("Run Data: %s" % data)
        # TODO hmmm. seems kind of confusing having run+net_id...and then a separate run_id that means a different thing
        self.db.index(index=self.task, doc_type="run%s" % self.net_id, id=id, body=data)

    def get_num_results(self):
        return self.db.search(index=self.task, doc_type="run%s" % self.net_id,
                              body={"query": {"match_all": {}}})["hits"]["total"]
