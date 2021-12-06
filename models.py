import datetime
from db import get_db_connection,close_db_connection

class Account:
    def __init__(self,id=None,pin=None,client_token=None):
        self.id = id
        self.pin = pin
        self.client_token = client_token
        self.conn = get_db_connection()
    
    def __del__(self):
        close_db_connection()
    
    def check_valid_token(self):
        acct = self.query_db("select acct_id,api_key,exp_date from accounts where acct_id=:acct_id",{"acct_id": self.id},one=True)
       
        if not acct or self.client_token!=acct["api_key"] or datetime.datetime.now() > datetime.datetime.strptime(acct["exp_date"],'%Y-%m-%d %H:%M:%S.%f'):
            return False

        return True
    
    def deposit(self,deposit_amount):
        cur = self.conn.cursor()
        cur.execute("update accounts set balance = balance + :balance where acct_id = :acct_id",
        {"balance":deposit_amount,"acct_id": self.id})
        cur.close()
 
    def withdraw(self,amount, is_overdraft=False):
        cur = self.conn.cursor()
        if is_overdraft:
            cur.execute("update accounts set balance = :balance  where acct_id = :acct_id",
            {"balance":amount,"acct_id": self.id})
            cur.close()
        else:
            cur.execute("update accounts set balance = balance - :balance  where acct_id = :acct_id",
            {"balance":amount,"acct_id": self.id})
            cur.close()

    def record_transaction(self,deposit_amount,new_balance,type):
        cur = self.conn.cursor()
        cur.execute("insert into transactions (acct_id,action_type,amount,balance,time_stamp) values(?,?,?,?,?)",
        (self.id,type,deposit_amount,new_balance,datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        cur.close()


    def update_atm_balance(self,amount,type):
        cur = self.conn.cursor()
        if type == "deposit":
            cur.execute("update atm set balance = balance + :balance",{"balance":amount})
            cur.close()
        elif type == "withdrawal":
            cur.execute("update atm set balance = balance - :balance",{"balance":amount})
            cur.close


    def get_acct_balance(self):
        acct_balance = self.query_db("select balance from accounts where acct_id=:acct_id",{"acct_id": self.id},one=True)[0]
        return acct_balance
    

    def get_transaction_history(self):
        result = self.query_db("select * from transactions where acct_id=:acct_id order by time_stamp desc",{"acct_id": self.id},one=False)
        if not result:
            return None
    
        return [{"timestamp": item["time_stamp"],"type":item["action_type"],"amount":item["amount"],"balance":item["balance"]} for item in result]


    def get_atm(self):
        result = self.query_db("select balance from atm",one=True)
        return result["balance"]

    
    def query_db(self,query, args={}, one=False):
        cur = self.conn.cursor()
        results = cur.execute(query, args).fetchall()
        cur.close()
        return (results[0] if results else None) if one else results


    @staticmethod
    def round_value(amount):
        return round(amount,2)




