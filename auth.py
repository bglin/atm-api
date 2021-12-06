from flask import request
from functools import wraps
from errors import custom_error_message
from models import Account

def authorize_user(f):
    @wraps(f)
    ## accepts args from app.route decorator
    def decorated_function(acct_id,*args,**kwargs):

        if not "Authorization" in request.headers:
            return custom_error_message("Not Authorized",401)
        
        data = request.headers["Authorization"]
        client_token = str.replace(str(data), 'Bearer ','')
        print(acct_id)
        print(client_token)
        user_account=Account(id = acct_id,client_token=client_token)

        # check if token exists for account and is not expired
        if not user_account.check_valid_token():
            return custom_error_message(" Not authorized. Token is invalid or expired",401)

        # return original view function
        return f(user_account,*args, **kwargs)            
    return decorated_function