import sqlite3

conn = sqlite3.connect("atm.db")

with open("schema.sql") as file:
    conn.executescript(file.read())

cur = conn.cursor()

#init atm balance
cur.execute("insert into atm (balance) values(10000)");

#init account balances
cur.execute("insert into accounts (acct_id,pin,balance) values(?,?,?)", ("2859459814","7386",10.24))
cur.execute("insert into accounts (acct_id,pin,balance) values(?,?,?)", ("1434597300","4557",90000.55))
cur.execute("insert into accounts (acct_id,pin,balance) values(?,?,?)", ("7089382418","0075",0.00))
cur.execute("insert into accounts (acct_id,pin,balance) values(?,?,?)", ("2001377812","5950",60.00))


conn.commit()
conn.close()


