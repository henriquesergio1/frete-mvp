
import os
import pyodbc
from contextlib import contextmanager

ERP_CONN_STR = os.getenv('ERP_SQL_CONN')
FRETE_CONN_STR = os.getenv('FRETE_SQL_CONN')

@contextmanager
def erp_conn():
    if not ERP_CONN_STR:
        raise RuntimeError("ERP_SQL_CONN não configurado")
    conn = pyodbc.connect(ERP_CONN_STR)
    try:
        yield conn
    finally:
        conn.close()

@contextmanager
def frete_conn():
    if not FRETE_CONN_STR:
        raise RuntimeError("FRETE_SQL_CONN não configurado")
    conn = pyodbc.connect(FRETE_CONN_STR)
    try:
        yield conn
    finally:
        conn.close()

def query_all(conn, sql, params=None):
    cur = conn.cursor()
    cur.execute(sql, params or [])
    cols = [c[0] for c in cur.description]
    rows = [dict(zip(cols, r)) for r in cur.fetchall()]
    cur.close()
    return rows

def query_one(conn, sql, params=None):
    cur = conn.cursor()
    cur.execute(sql, params or [])
    row = cur.fetchone()
    cur.close()
    if row is None:
        return None
    cols = [c[0] for c in cur.description]
    return dict(zip(cols, row))

def execute(conn, sql, params=None):
    cur = conn.cursor()
    cur.execute(sql, params or [])
    conn.commit()
    cur.close()

def executemany(conn, sql, params_seq):
    cur = conn.cursor()
    cur.executemany(sql, params_seq)
    conn.commit()
    cur.close()
