# coding=utf-8
import json

import elasticsearch

from spidercommon.model import Page, File, session_scope
from spidercommon.model.elasticsearch import (PageDocument, get_client,
                                              get_index)
from spidercommon.tasks import WorkerTask, celery
from spidercommon.util.text import CustomJSONEncoder


@celery.task(base=WorkerTask)
def populate_elasticsearch():
    elastic_db = get_client()
    state = {
        "bulks": [],
        "approx_bulk_size": 0,
    }

    # This is terrible but we have to ping the index to set it inside the PageDocument.
    get_index()

    with session_scope() as sql_db:
        for page in sql_db.query(File).yield_per(1000):
            # Convert the page to a bulk insert object and add it to the queue.
            elastic_page = PageDocument.from_obj(page)
            state["bulks"].append(elastic_page.to_dict(include_meta=True))
            state["approx_bulk_size"] += len(json.dumps(state["bulks"][-1], cls=CustomJSONEncoder))

            # Push off when the bulks is about 10 MB
            if state["approx_bulk_size"] > (1024 * 10):
                elasticsearch.helpers.bulk(elastic_db, state["bulks"])
                state["bulks"].clear()
                state["approx_bulk_size"] = 0
