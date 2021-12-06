from flask import g,current_app
import sqlite3
import datetime
from config import Config

#db connection
def get_db_connection():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(Config.DATABASE_URL)
        db.row_factory = sqlite3.Row
       
    return db

def close_db_connection():
    db = getattr(g, '_database', None)
    if db is not None:
        print("closing db connection")
        db.close()


def init_testdb():
    db = get_db_connection()
    with current_app.open_resource("schema.sql") as file:
        db.executescript(file.read().decode("utf8"))

def add_test_data():
    db = get_db_connection()
    cur = db.cursor()

    #init atm balance
    cur.execute("insert into atm (balance) values(10000)")

    #init account balances
    cur.execute("insert into accounts (acct_id,pin,balance) values(?,?,?)", ("2859459814","7386",10.24))
    cur.execute("insert into accounts (acct_id,pin,balance) values(?,?,?)", ("1434597300","4557",90000.55))
    cur.execute("insert into accounts (acct_id,pin,balance) values(?,?,?)", ("7089382418","0075",0.00))
    cur.execute("insert into accounts (acct_id,pin,balance) values(?,?,?)", ("2001377812","5950",60.00))


    # test transactions
    cur.execute("insert into transactions (acct_id,action_type,amount,balance,time_stamp) values(?,?,?,?,?)",
        ("2001377812","deposit",10,20,'2021-09-05 21:50:48'))
    cur.execute("insert into transactions (acct_id,action_type,amount,balance,time_stamp) values(?,?,?,?,?)",
        ("2001377812","deposit",40,60,'2021-09-06 21:50:48'))
    cur.execute("insert into transactions (acct_id,action_type,amount,balance,time_stamp) values(?,?,?,?,?)",
        ("2001377812","deposit",20,80,'2021-09-07 21:50:48'))
    cur.execute("insert into transactions (acct_id,action_type,amount,balance,time_stamp) values(?,?,?,?,?)",
        ("2001377812","withdrawal",20,60,'2021-09-08 21:50:48'))

    # set valid api key for test accounts
    cur.execute("update accounts set api_key = :api_key, exp_date = :exp_date where acct_id = :acct_id",
                {"api_key": "test_valid_key","exp_date":datetime.datetime.now() + datetime.timedelta(seconds = 60000), "acct_id": "2859459814"})
    
    cur.execute("update accounts set api_key = :api_key, exp_date = :exp_date where acct_id = :acct_id",
                {"api_key": "test_valid_key_2","exp_date":datetime.datetime.now() + datetime.timedelta(seconds = 60000), "acct_id": "2001377812"})

    cur.execute("update accounts set api_key = :api_key, exp_date = :exp_date where acct_id = :acct_id",
                {"api_key": "test_valid_key_3","exp_date":datetime.datetime.now() + datetime.timedelta(seconds = 60000), "acct_id": "1434597300"})
    #set expired key
    cur.execute("update accounts set api_key = :api_key, exp_date = :exp_date where acct_id = :acct_id",
                {"api_key": "test_expired_key","exp_date":datetime.datetime.now() - datetime.timedelta(seconds = 60000), "acct_id": "7089382418"})
    

    db.commit()
    db.close()