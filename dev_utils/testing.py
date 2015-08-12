from __future__ import (absolute_import, print_function)

import sys

import mongoengine.connection

from ..db_lib import (db_connect, db_disconnect)


mongo_conn = None
db_name = None
db_host = None

def dbtest_setup(collections):
    """
    """
    global mongo_conn, db_name, db_host

    db_disconnect(collections)
    print('connecting', file=sys.stderr)
    (mongo_conn, db_name, db_host) = db_connect()
        

def dbtest_teardown(collections, drop_db=True):
    """
    """
    
    if drop_db != False:
        print('dropping', file=sys.stderr)
        mongo_conn.drop_database(db_name)

    print('disconnecting', file=sys.stderr)
    db_disconnect(collections)

    
