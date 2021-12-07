from flask import Flask,request
from db import get_db_connection
from config import Config
from auth import authorize_user
from errors import custom_error_message
import secrets
import datetime


def create_app(test_config=None):
    
    app = Flask(__name__)

    if test_config:
         app.config.update(test_config)

    else:
        app.config.from_object(Config)
    
    @app.route("/")
    def index():
        return {"message":"Welcome to the ATM API Demo"}


    # account balance 
    @app.route("/api/accounts/<acct_id>/balance",methods = ["GET"])
    @authorize_user
    def get_balance(user_account):

        if request.method != "GET":
            return custom_error_message("Method not allowed",405)

        #query account 
        balance = user_account.get_acct_balance()
        id = user_account.id
        return {"account_id":id,"balance":user_account.round_value(balance)}

    #transaction history
    @app.route("/api/accounts/<acct_id>/history", methods = ["GET"])
    @authorize_user
    def get_history(user_account):
        
        if request.method != "GET":
            return custom_error_message("Method not allowed",405)
            
        history = user_account.get_transaction_history()
        if not history:
            return {"message": "No history found"}
        
        return {"account_id":user_account.id,"history": history}

    #withdraw
    # the machine only contains $20 bills
    @app.route("/api/accounts/<acct_id>/withdraw",methods = ["POST"])
    @authorize_user
    def withdraw(user_account):

        if request.method != "POST":
            return custom_error_message("Method not allowed",405)

        if not request.get_json():
            return custom_error_message("Content-Type must be application/json",400)
        
        withdrawal_amount = request.get_json()["amount"]

        #validation
        if type(withdrawal_amount) == str or withdrawal_amount is None:
            return custom_error_message("Please provide a valid number of type int or float",400)
        
            
        if withdrawal_amount < 0:
            return custom_error_message("Please provide a positive float",400)

        #check if withdrawal is multiple of 20
        if abs(withdrawal_amount) % 20 != 0:
            return custom_error_message("withdrawal amount must be in multiples of $20",400)

    
        conn = get_db_connection()
        cur = conn.cursor()

        json_response = {"message":""}
        # case 1 no money in the machine
        atm_balance = cur.execute("select balance from atm").fetchone()["balance"]

        if atm_balance <=0:
            return custom_error_message("Unable to process your withdrawal at this time",503)

    

        #case 2 account overdrawn (balance is negative). no withdraw allowed 
        acct_balance = user_account.get_acct_balance()
        if acct_balance < 0:
            return custom_error_message("Your account is overdrawn! You may not make withdrawals at this time.",400)
    
        # if not enough money in machine,the withdrawal amount should be adjusted to be the amount in the machine
        if  withdrawal_amount > atm_balance:
            withdrawal_amount = atm_balance
            json_response["message"] = "Unable to dispense full amount requested at this time."

        #case 3 not enough money in the account. dispense amount requested and remove $5 + amount overdraft
        if withdrawal_amount > acct_balance:
            #update account balance
            overdraft_amt = -abs( withdrawal_amount - acct_balance + 5)
            try:
                user_account.withdraw(overdraft_amt,is_overdraft = True)
    

                #update atm balance
                user_account.update_atm_balance(withdrawal_amount,type="withdrawal")
                
                #record transaction
                user_account.record_transaction(withdrawal_amount,user_account.get_acct_balance(),type="withdrawal")
            
            
                user_account.conn.commit()
                
                json_response["message"] = " ".join([json_response["message"],"You have been charged an overdraft fee of $5."])
                json_response["amount_dispensed"] = withdrawal_amount
                json_response["current_balance"] = user_account.get_acct_balance()
                return json_response

            except Exception as e:
                user_account.conn.rollback()
                error = " ".join(["there was an error processing your request",str(e)])
                return custom_error_message(error,500)

            

        #case 4(happy path) withdraw money
        if withdrawal_amount <=  acct_balance:
            try:
                # update acct balance
                user_account.withdraw(withdrawal_amount,is_overdraft = False)
              

                #update atm balance
                user_account.update_atm_balance(withdrawal_amount,type="withdrawal")
            
                
              
                #record transaction
                user_account.record_transaction(withdrawal_amount,user_account.get_acct_balance(),type="withdrawal")
               
                user_account.conn.commit()

                json_response["message"] = (json_response["message"] or "Your withdrawal was successful")
                json_response["amount_dispensed"] = withdrawal_amount
                json_response["current_balance"] = user_account.round_value(user_account.get_acct_balance())
                return json_response

            except Exception as e:
                user_account.conn.rollback()
                error = " ".join(["there was an error processing your request:",(str(e))])
                return custom_error_message(error,500)


    #deposit
    @app.route("/api/accounts/<acct_id>/deposit", methods = ["POST"])
    @authorize_user
    def deposit(user_account):
        
        if request.method != "POST":
            return custom_error_message("Method not allowed",405)

        if not request.get_json():
            return custom_error_message("Content-Type must be application/json",400)

        deposit_amount = request.get_json()["amount"]

        #validation
        if type(deposit_amount) == str or deposit_amount is None:
            return custom_error_message("Please provide a valid number of type int or float",400)
            
        if deposit_amount < 0:
            return custom_error_message("Please provide a positive float",400)

        try:
            
            # update account
            user_account.deposit(deposit_amount)
            
            #update atm cash balance
            user_account.update_atm_balance(deposit_amount,type = "deposit")
        

            # record transaction
            user_account.record_transaction(deposit_amount,user_account.get_acct_balance(),type="deposit")

            user_account.conn.commit()

            return {"message":"Current balance:{}".format(user_account.round_value(user_account.get_acct_balance()))}

        except Exception as e:
            user_account.conn.rollback()
        
            error = " ".join(["there was an error processing your request:",str(e)])
            return custom_error_message(error,500)


    # logout - delete token from account
    @app.route("/api/auth/logout",methods =["POST"])
    def logout():

        if request.method != "POST":
            return custom_error_message("Method not allowed",405)

        user_creds = request.get_json()
            
        if not user_creds:
            return custom_error_message("Content-Type must be application/json",400)

        #sanitize inputs
        user_creds["acct_id"] = user_creds["acct_id"].strip()
        user_creds["pin"] = user_creds["pin"].strip()

        #validation
        if not len(user_creds["acct_id"]) == 10 or not len(user_creds["pin"]) == 4 or user_creds["acct_id"] is None or user_creds["pin"] is None:
            return custom_error_message("Invalid creds or missing",400)

        conn = get_db_connection()
        cur = conn.cursor()

        #account lookup
        try:
            acct = cur.execute("select acct_id, pin,api_key from accounts where acct_id = :acct_id",{"acct_id": user_creds["acct_id"]}).fetchone()
        except Exception as e:
            error = " ".join(["there was an error processing your request:",str(e)])
            return custom_error_message(error,500)

        if not acct:
            return custom_error_message("Authorization failed. account {} does not exist".format(user_creds["acct_id"]),404)

        if not acct["pin"] == user_creds["pin"]:
            return custom_error_message("Authorization failed. incorrect pin",400)

        # revoke token
        try:
            cur.execute("update accounts set api_key = null, exp_date = null where acct_id = :acct_id",{"acct_id": acct["acct_id"]})
            conn.commit()

            return {"message":"Account {} logged out. All tokens revoked".format(acct["acct_id"])}
        except Exception as e:
            error = " ".join(["there was an error processing your request:",str(e)])
            return custom_error_message(error,500)

        

    #auth - get token
    @app.route("/api/auth/token", methods =["POST"])
    def get_auth_key():

        if request.method != "POST":
            return custom_error_message("Method not allowed",405)

        user_creds = request.get_json()
        if not user_creds:
            return custom_error_message("Content-Type must be application/json",400)

        #sanitize inputs
        user_creds["acct_id"] = user_creds["acct_id"].strip()
        user_creds["pin"] = user_creds["pin"].strip()

        #validation
        if not len(user_creds["acct_id"]) == 10 or not len(user_creds["pin"]) == 4 or user_creds["acct_id"] is None or user_creds["pin"] is None:
            return custom_error_message("Invalid creds or missing",400)

        conn = get_db_connection()
        cur =conn.cursor()
        try:
            acct = cur.execute("select acct_id, pin from accounts where acct_id = :acct_id",{"acct_id": user_creds["acct_id"]}).fetchone()
        except Exception as e:
            error = " ".join(["there was an error processing your request:",str(e)])
            return custom_error_message(error,500)
        
        if not acct:
            #404
            return custom_error_message("Authorization failed. account {} does not exist".format(user_creds["acct_id"]),404)
        
        if not acct["pin"] == user_creds["pin"]:
            return custom_error_message("Authorization failed. incorrect pin",400)
        else:
            #set api key as random string
            key = secrets.token_hex(16)
            exp_date = datetime.datetime.now() + datetime.timedelta(seconds = 120)

            try:
                cur.execute("update accounts set api_key = :api_key, exp_date = :exp_date where acct_id = :acct_id",
                {"api_key": key,"exp_date":exp_date, "acct_id": acct["acct_id"]})

                conn.commit()
                return {"message": "{} successfully authorized".format(user_creds["acct_id"])
                ,"api_key":key,"expiration_datetime": exp_date}
            except Exception as e:
                conn.rollback()
                error = " ".join(["there was an error processing your request:",str(e)])
                return custom_error_message(error,500)

            
    #shut down server
    @app.route("/end", methods = ["POST"])
    def end_session():

        if request.method != "POST":
            return custom_error_message("Method not allowed",405)

        shutdown_func = request.environ.get('werkzeug.server.shutdown')
        if shutdown_func is None:
            raise RuntimeError('Not running werkzeug')
        shutdown_func()
        return "End command received shutting down server. "


    return app