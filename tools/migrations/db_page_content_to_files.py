import time
from spidercommon.model import sm, Page, File
from spidercommon.util.storage import HashedFile
from sqlalchemy.dialects.postgresql import insert

db = sm()
meta = {"i": 0}

for page in db.query(Page).yield_per(1000):
    page_content = page.content

    file_row = db.query(File).filter(File.url == page.url).scalar()

    if not file_row:
        statement = insert(File).values(
            url=page.url,
            domain_id=page.domain_id,
            last_crawl=page.last_crawl,
            size=len(page_content),
            path=page.path
        ).on_conflict_do_nothing(index_elements=["url"])
        db.execute(statement)
        file_row = db.query(File).filter(File.url == page.url).scalar()

    file_row.content = page_content

    meta["i"] += 1
    if meta["i"] % 100 == 0:
        db.commit()
        print(f"{meta['i']} completed.")

db.commit()
