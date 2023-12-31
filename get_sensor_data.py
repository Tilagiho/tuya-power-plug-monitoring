import time
import hashlib
import json
import hmac
from typing import Any
from pprint import pprint
import requests
from datetime import datetime, timedelta
import csv
import os
import sys
from suntimes import SunTimes
import pytz

from env import ENDPOINT, ACCESS_ID, ACCESS_KEY, DEVICE_ID, COLUMN_ORDER, LONGITUDE, LATITUDE, ALTITUDE, TZ_NAME, DATA_DIR

# request variables
access_token = ""
t_access_token = -1
expire_time = -1
refresh_token = ""

# prepare variables for sunrise and sunset calculation
sleep_td = timedelta(hours=1)
sun = SunTimes(longitude=LONGITUDE, latitude=LATITUDE, altitude=ALTITUDE)
day = datetime.now().date()
sunrise = sun.risewhere(day, TZ_NAME).astimezone(pytz.utc)
sunset = sun.setwhere(day, TZ_NAME).astimezone(pytz.utc)

print(f"sunrise: {sunrise}")
print(f"sunset: {sunset}")

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

def get_sleep_time():
    dt = datetime.utcnow().astimezone(pytz.utc)
    # well before sunrise
    if dt < (sunrise - 2 * sleep_td):
        return 600
    # before sunrise
    if dt < (sunrise - sleep_td):
        return 300
    # well after sunset
    elif dt > (sunset + 2 * sleep_td):
        return -1 # end script
    # after sunset
    elif dt > (sunset + sleep_td):
        return 300
    # during day
    else:
        return 15

def access_token_valid():
    t = int(time.time())
    return (access_token != "") and (t - (t_access_token/1000) < expire_time - 100)

def access_token_refreshable():
    t = int(time.time())
    return (access_token != "") and (t - (t_access_token/1000) < expire_time - 10)

def get_access_token_request_path(get_new_token):
    if get_new_token:
        request_path = "/v1.0/token?grant_type=1"
    else:
        request_path = f"/v1.0/token/{refresh_token}"

    return request_path

def update_access_token():
    global access_token, t_access_token, expire_time, refresh_token
    # send request
    attempts = 0
    while attempts < 100:
        get_new_token = not access_token_refreshable()
        request_path = get_access_token_request_path(get_new_token)

        if get_new_token:
            print("Getting new token...")
        else:
            print("Refreshing token...")

        response = send_request(request_path, "GET", access_token="")
        json_data = response.json()

        if response.status_code == 200 and json_data['success']:
            break
        else:
            print("Access token request not successfull:")
            print(json_data)
            print()
            attempts += 1
            time.sleep(15)

    if not (response.status_code == 200 and json_data['success']):
        raise RuntimeError("No connection possible.")

    print("Success.")
    print()
    # update access token info
    access_token = json_data['result']['access_token']
    t_access_token = json_data['t']
    expire_time = int(json_data['result']['expire_time'])
    refresh_token = json_data['result']['refresh_token']

# get device info
while True:
    # get access token if necessary
    if not access_token_valid():
        update_access_token()

    # pprint(datetime.now())
    response = send_request(f"/v1.0/devices/{DEVICE_ID}", "GET", access_token)
    json_data = response.json()

    # response error:
    # sleep and then skip
    if response.status_code != 200 or not json_data['success']:
        print("Error reaching server.")
        print(json_data)
        print()
        time.sleep(15)
        continue

    # get data from request
    sensor_value_dict = {elem['code']: elem['value'] for elem in json_data['result']['status']}
    sensor_value_dict['online'] = json_data['result']['online']
    sensor_value_dict['t'] = json_data['t']

    date = datetime.now()
    file_path = f"{DATA_DIR}/{date.year}{str(date.month).zfill(2)}{str(date.day).zfill(2)}_sensor_data.csv"
    append_to_csv(sensor_value_dict, file_path)

    sleep_time = get_sleep_time()
    if sleep_time < 0:
        print("Sun is well set. Ending script.")
        sys.exit()

    time.sleep(sleep_time)