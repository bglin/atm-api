# helpers
def get_auth_token(client,acct_id,pin):
    acct_id = acct_id
    pin = pin
    return client.post('/api/auth/token',json={"acct_id":acct_id,"pin":pin})

def revoke_auth_token(client,acct_id,pin):
    acct_id = acct_id
    pin = pin
    return client.post('/api/auth/logout',json={"acct_id":acct_id,"pin":pin})



def test_index_endpoint(client):
    """Test index endpoint returns correct response."""

    res = client.get('/')
    json_data = res.get_json()

    assert res.status_code == 200
    assert json_data =={"message":"Welcome to the ATM API Demo"}

def test_get_acct_balance(client):

    acct_id = "2001377812"
    valid_token_2="test_valid_key_2"
    url = '/api/accounts/{}/balance'.format(acct_id)
    res = client.get(url, headers = {"Authorization": 'Bearer {}'.format(valid_token_2)})
    json_data = res.get_json()

    assert res.status_code == 200
    assert json_data["balance"] == 60.00


def test_get_acct_history_available(client):

    # history available
    acct_id = "2001377812"
    valid_token_2="test_valid_key_2"
    url = '/api/accounts/{}/history'.format(acct_id)
    res = client.get(url, headers = {"Authorization": 'Bearer {}'.format(valid_token_2)})
    json_data = res.get_json()
    assert res.status_code == 200

    assert json_data["history"]
    assert len(json_data["history"]) == 4

def test_get_acct_history_unavailable(client):
    # no history found
    acct_id = "2859459814"
    valid_token="test_valid_key"
    url = '/api/accounts/{}/history'.format(acct_id)
    res = client.get(url, headers = {"Authorization": 'Bearer {}'.format(valid_token)})
    json_data = res.get_json()

    assert res.status_code == 200
    assert json_data["message"] == "No history found"

def test_acct_deposit(client):
    acct_id = "2859459814"
    valid_token="test_valid_key"
    url = '/api/accounts/{}/deposit'.format(acct_id)
    res = client.post(url,json ={"amount": 30},headers = {"Authorization": 'Bearer {}'.format(valid_token)})
    
    json_data =res.get_json()

    assert res.status_code == 200
    assert '40.24' in json_data["message"]

def test_acct_deposit_validations(client):
    acct_id = "2859459814"
    valid_token="test_valid_key"
    url = '/api/accounts/{}/deposit'.format(acct_id)
    # negative amount
    res = client.post(url,json ={"amount": -30},headers = {"Authorization": 'Bearer {}'.format(valid_token)})
    json_data =res.get_json()
    assert res.status_code == 400
    assert json_data["message"] == "Please provide a positive float"

    #invalid type
    res = client.post(url,json ={"amount": "30"},headers = {"Authorization": 'Bearer {}'.format(valid_token)})
    json_data =res.get_json()
    assert res.status_code == 400
    assert json_data["message"] == "Please provide a valid number of type int or float"

def test_acct_withdrawal_validations(client):

    acct_id = "2859459814"
    valid_token="test_valid_key"
    url = '/api/accounts/{}/withdraw'.format(acct_id)

    #multiple of $20
    res = client.post(url,json ={"amount": 10},headers = {"Authorization": 'Bearer {}'.format(valid_token)})
    json_data = res.get_json()
    assert res.status_code == 400
    assert json_data["message"] == "withdrawal amount must be in multiples of $20"

    # negative amount
    res = client.post(url,json ={"amount": -10},headers = {"Authorization": 'Bearer {}'.format(valid_token)})
    json_data = res.get_json()
    assert res.status_code == 400
    assert json_data["message"] == "Please provide a positive float"

     # invalid type
    res = client.post(url,json ={"amount": "10"},headers = {"Authorization": 'Bearer {}'.format(valid_token)})
    json_data = res.get_json()
    assert res.status_code == 400
    assert json_data["message"] == "Please provide a valid number of type int or float"

def test_acct_withdrawal_overdraft(client):
    acct_id = "2859459814"
    valid_token="test_valid_key"
    url = '/api/accounts/{}/withdraw'.format(acct_id)
    # overdraft fee
    res = client.post(url,json ={"amount": 10000},headers = {"Authorization": 'Bearer {}'.format(valid_token)})
    json_data = res.get_json()
    assert res.status_code == 200
    assert json_data["message"] == " You have been charged an overdraft fee of $5."

def test_acct_withdrawal_atm_balance_is_zero(client): 
    acct_id = "2859459814"
    valid_token="test_valid_key"
    url = '/api/accounts/{}/withdraw'.format(acct_id)
 
    client.post(url,json ={"amount": 10000},headers = {"Authorization": 'Bearer {}'.format(valid_token)})
    # atm balance <=0
    res = client.post(url,json ={"amount": 20},headers = {"Authorization": 'Bearer {}'.format(valid_token)})
    json_data = res.get_json()
    assert res.status_code == 503
    assert json_data["message"] =="Unable to process your withdrawal at this time"

def test_acct_no_withdrawal_allowed(client):
    # overdraft no withdrawal allowed

    acct_id = "2859459814"
    valid_token="test_valid_key"
    url = '/api/accounts/{}/withdraw'.format(acct_id)
    # overdraft fee
    client.post(url,json ={"amount": 10000},headers = {"Authorization": 'Bearer {}'.format(valid_token)})
    # add money since atm balance is 0. acct will still be in withdrawal
    client.post('/api/accounts/{}/deposit'.format(acct_id),json={"amount":20},headers = {"Authorization": 'Bearer {}'.format(valid_token)})

    res = client.post(url,json ={"amount": 20},headers = {"Authorization": 'Bearer {}'.format(valid_token)})
    json_data =res.get_json()
    assert res.status_code == 400
    assert json_data["message"] == "Your account is overdrawn! You may not make withdrawals at this time."
    
def test_acct_withdrawal_success(client):
    acct_id = "2859459814"
    valid_token="test_valid_key"
    url = '/api/accounts/{}/withdraw'.format(acct_id)

    ## add money to cover withdrawal
    client.post('/api/accounts/{}/deposit'.format(acct_id),json={"amount":20000},headers = {"Authorization": 'Bearer {}'.format(valid_token)})
   
    # successful withdrawal
    res = client.post(url,json ={"amount": 20},headers = {"Authorization": 'Bearer {}'.format(valid_token)})
    json_data =res.get_json()
    assert res.status_code == 200
    assert json_data["amount_dispensed"] == 20
    assert json_data["message"] == "Your withdrawal was successful"

def test_acct_withdrawal_adjust_balance(client):
    '''adjust withdrawal balance to atm balance'''

    acct_id = "1434597300"
    valid_token = "test_valid_key_3"
    #deplete atm funds
    client.post('/api/accounts/{}/withdraw'.format(acct_id),json={"amount":9980},headers = {"Authorization": 'Bearer {}'.format(valid_token)})

    acct_id ="2001377812"
    valid_token = "test_valid_key_2"

    res = client.post('/api/accounts/{}/withdraw'.format(acct_id),json={"amount":40},headers = {"Authorization": 'Bearer {}'.format(valid_token)})
    json_data =res.get_json()

    assert res.status_code == 200
    assert json_data["message"] == "Unable to dispense full amount requested at this time."
    assert json_data["amount_dispensed"] == 20
    assert json_data["current_balance"] == 40
    
def test_authenticated_api_call(client):
    '''Test authentication decorator logic when calling a protected api endpoint'''
   
    #valid token
    acct_id = "2859459814"
    valid_token="test_valid_key"
    url = '/api/accounts/{}/balance'.format(acct_id)
    res = client.get(url, headers = {"Authorization": 'Bearer {}'.format(valid_token)})
    assert res.status_code == 200


    #No auth header present
    res = client.get(url)

    assert res.status_code == 401
    assert res.get_json()["message"] == "Not Authorized"


    #expired token
    acct_id = "7089382418"
    expired_token = "test_expired_key"
    res = client.get(url, headers = {"Authorization": 'Bearer {}'.format(expired_token)})

    assert res.status_code == 401

    
def test_login(client):
    """Test api/auth/token endpoint."""
    acct_id = "2859459814"
    pin = "7386"
    
    # valid creds
    res = get_auth_token(client,acct_id,pin)
    json_data = res.get_json()
    
    assert res.status_code == 200
    assert json_data["message"] == "{} successfully authorized".format(acct_id)
    assert json_data["api_key"] is not None
    assert json_data["expiration_datetime"] is not None

    # format of creds does not match predefined schema
    acct_id = "3231"
    pin ="11111111111"
    res = get_auth_token(client,acct_id,pin)
    json_data = res.get_json()
    assert res.status_code == 400
    assert json_data["message"] == "Invalid creds or missing"

    # acct doesnt exist
    acct_id = "3859459817"
    pin = "7386"

    res = get_auth_token(client,acct_id,pin)
    json_data = res.get_json()
    assert res.status_code == 404
    assert json_data["message"] == "Authorization failed. account {} does not exist".format(acct_id)

    # pin number incorrect
    acct_id = "2859459814"
    pin = "7383"

    res = get_auth_token(client,acct_id,pin)
    json_data = res.get_json()
    assert res.status_code == 400
    assert json_data["message"] == "Authorization failed. incorrect pin"

    # invalid method
    res = client.get('/api/auth/token')
    assert res.status_code == 405


def test_logout(client):
    """Test api/auth/logout endpoint."""
    # valid creds
    acct_id = "2859459814"
    pin = "7386"
    res = revoke_auth_token(client,acct_id,pin)
    json_data = res.get_json()
    
    assert res.status_code == 200
    assert json_data["message"] == "Account {} logged out. All tokens revoked".format(acct_id)

    acct_id = "3231"
    pin ="11111111111"
    res = revoke_auth_token(client,acct_id,pin)
    json_data = res.get_json()
    assert res.status_code == 400
    assert json_data["message"] == "Invalid creds or missing"

     # acct doesnt exist
    acct_id = "3859459817"
    pin = "7386"

    res = revoke_auth_token(client,acct_id,pin)
    json_data = res.get_json()
    assert res.status_code == 404
    assert json_data["message"] == "Authorization failed. account {} does not exist".format(acct_id)

    # pin number incorrect
    acct_id = "2859459814"
    pin = "7383"

    res = revoke_auth_token(client,acct_id,pin)
    json_data = res.get_json()
    assert res.status_code == 400
    assert json_data["message"] == "Authorization failed. incorrect pin"

    # invalid method
    res = client.get('/api/auth/logout')
    assert res.status_code == 405


 
