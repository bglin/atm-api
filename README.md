# ATM API 

This is a sample API service that models functionality of an ATM. 

## Prerequisites
- latest version of [Python 3.9](https://www.python.org/downloads/release/python-390/) installed
- [pip](https://pip.pypa.io/en/stable/) 
- [venv](https://docs.python.org/3/library/venv.html)

## Installation

```sh
$ git clone https://github.com/bglin/atm-api.git atm-api
$ cd atm-api
$ python3.9 -m venv venv
$ source venv/bin/activate
$ pip install -r requirements.txt
```
## Run Development Server
with the virtual env activated run the following -

```sh
(venv) $ run_app.sh
```
- The api service will now be running on `localhost:5000`
- The api service is preloaded with test account data. Use any of the following Account ID/Pin combination to retrieve an auth token for that account

| Account ID  |    Pin     |Balance     |
| ----------- | -----------| ------------|
| "2859459814"| "7386"     |    10.24     |
| "1434597300"| "4557"     |    90000.55  |
| "7089382418"| "0075"     |    0.00      |
| "2001377812"| "5950"     |    60.00     |

## Authentication
All endpoints except `api/auth/token` and `api/auth/logout` require a valid token in the header of the request. A token can be retrieved via the `api/auth/token` endpoint
```python
import requests
import json

url = "localhost:5000/api/auth/token"

payload = json.dumps({
  "acct_id": "2859459814",
  "pin": "7386"
})
headers = {
  'Content-Type': 'application/json'
}

response = requests.request("POST", url, headers=headers, data=payload)
```

**Success Response 200**:

```json
{"message": "2859459814 successfully authorized",
"api_key":"046a6dc260cd9a158f7838acf205a873",
"expiration_datetime": "2021-12-06 15:35:20"}

```
## Example Authenticated Request 

```python
import requests
import json

url = "localhost:5000/api/accounts/2859459814/deposit"

payload = json.dumps({
  "amount": 10
})
headers = {
  'Authorization': 'Bearer e025be18a241e69835b3716397f3dd66',
  'Content-Type': 'application/json'
}

response = requests.request("POST", url, headers=headers, data=payload)
```
**Success Response 200**:
```json
{"message":"Current balance: 40.00"}
```
## Endpoints

*  `POST /api/auth/token`
*  `POST /api/auth/logout`
*  `POST /api/accounts/:acct_id/deposit`
    - **request body**
    ```
    {
        "amount": 10
    }
    ```
*  `POST /api/accounts/:acct_id/withdraw`
    - **request body**
        ```
        {
            "amount": 10
        }
        ```
*  `GET /api/accounts/:acct_id/balance`
*  `GET /api/accounts/:acct_id/history`
*  `POST /end`

## Tests
 Tests are located in `test_app.py`. To run tests, execute `pytest`

```sh
$ pytest
```

