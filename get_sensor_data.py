import time
import hashlib
import json
import hmac
from typing import Any
from pprint import pprint
import requests
from datetime import datetime
import csv
import os

from env import ENDPOINT, ACCESS_ID, ACCESS_KEY, USERNAME, PASSWORD, DEVICE_ID, COLUMN_ORDER


def calculate_sign(
        access_id: str,
        access_secret: str,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        body: dict[str, Any] | None = None,
        access_token: str = None,
    ) -> tuple[str, int]:

    # HTTPMethod
    str_to_sign = method
    str_to_sign += "\n"

    # Content-SHA256
    content_to_sha256 = (
        "" if body is None or len(body.keys()) == 0 else json.dumps(body)
    )

    str_to_sign += (
        hashlib.sha256(content_to_sha256.encode("utf8")).hexdigest().lower()
    )
    str_to_sign += "\n"

    # Header
    str_to_sign += "\n"

    # URL
    str_to_sign += path

    if params is not None and len(params.keys()) > 0:
        str_to_sign += "?"

        params_keys = sorted(params.keys())
        query_builder = "".join(f"{key}={params[key]}&" for key in params_keys)
        str_to_sign += query_builder[:-1]

    # Sign
    t = int(time.time() * 1000)

    message = access_id
    if access_token is not None and access_token != "":
        message += access_token
    message += str(t) + str_to_sign

    sign = (
        hmac.new(
            access_secret.encode("utf8"),
            msg=message.encode("utf8"),
            digestmod=hashlib.sha256,
        )
        .hexdigest()
        .upper()
    )
    return sign, str(t)

def send_request(request_path, method, access_token, ):
    request_url = f"{ENDPOINT}{request_path}"
    sign, t = calculate_sign(ACCESS_ID, ACCESS_KEY, method, request_path, access_token=access_token)
    headers = {
        "client_id": ACCESS_ID,
        "sign": sign,
        "sign_method": "HMAC-SHA256",
        "access_token": access_token,
        "t": str(t),
        "lang": "en",
    }

    if method == "GET":
        response = requests.get(request_url, headers=headers)
    elif method == "POST":
        response = requests.post(request_url, headers=headers)
    else:
        raise NotImplementedError(f"Method \"{method}\" is not implemented.")
    
    return response

def append_to_csv(value_dict, file_path):
    # Check if file exists and if it is empty
    file_exists = os.path.isfile(file_path)
    file_empty = not file_exists or os.stat(file_path).st_size == 0

    # Open the file in append mode
    with open(file_path, 'a', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=COLUMN_ORDER + list(set(value_dict.keys())-set(COLUMN_ORDER)))

        # Write the header only if the file is new or empty
        if file_empty:
            writer.writeheader()

        # Append the dictionary as a new row
        writer.writerow(value_dict)


# get access token
response = send_request("/v1.0/token?grant_type=1", "GET", access_token="")
json_data = response.json()

access_token = json_data['result']['access_token']
t_access_token = json_data['t']
expire_time = int(json_data['result']['expire_time'])
refresh_token = json_data['result']['refresh_token']

pprint(json_data)
print()
# get device info
while True:
    # pprint(datetime.now())
    response = send_request(f"/v1.0/devices/{DEVICE_ID}", "GET", access_token)

    if response.status_code == 200:
        json_data = response.json()

        # get data from request
        sensor_value_dict = {elem['code']: elem['value'] for elem in json_data['result']['status']}
        sensor_value_dict['online'] = json_data['result']['online']
        sensor_value_dict['t'] = json_data['t']

        date = datetime.now()
        file_path = f"data/{date.year}{date.month}{date.day}_sensor_data.csv"
        append_to_csv(sensor_value_dict, file_path)

        # refresh access token if necessary
        if (sensor_value_dict['t'] - t_access_token)/1000 > (expire_time - 1000):
            print("Trying to refresh access token...")
            response = send_request(f"/v1.0/token/{refresh_token}", "GET", "")
            json_data = response.json()

            if not json_data['success']:
                print(json_data)
                raise RuntimeError("Error: Token refreshing not successfull!")

            print("Success!")
            access_token = json_data['result']['access_token']
            expire_time = json_data['result']['expire_time']
            refresh_token = json_data['result']['refresh_token']
    else:
        print("Response error:")
        pprint(response)
        print()

    time.sleep(15)