import keyring as kr
from getpass import getpass

# online
ACCESS_ID = kr.get_password("Tuya","access_id") # your_access_id
ACCESS_KEY = kr.get_password("Tuya","secret") # your_access_key
USERNAME = kr.get_password("Tuya","username") # your_username
PASSWORD = kr.get_password("Tuya", "password") # your_password
DEVICE_ID = kr.get_password("Tuya","device_id") # your_device_id
ENDPOINT = "https://openapi.tuyaeu.com"

# csv settings
COLUMN_ORDER = ['t', 'online', 'relay_status', 'countdown_1', 'switch_1', 'cur_voltage', 'cur_current', 'cycle_time', 'cur_power', 'add_ele', 'random_time']

if ACCESS_ID is None:
    ACCESS_ID = input("Please enter access id: ")
    kr.set_password("Tuya", "access_id", ACCESS_ID)
if ACCESS_KEY is None:
    ACCESS_KEY = getpass("Please enter access key (secret): ")
    kr.set_password("Tuya", "secret", ACCESS_KEY)
if USERNAME is None:
    USERNAME = input("Please enter username: ")
    kr.set_password("Tuya", "username", USERNAME)
if PASSWORD is None:
    PASSWORD = getpass("Please enter account password: ")
    kr.set_password("Tuya", "password", PASSWORD)
if DEVICE_ID is None:
    DEVICE_ID = input("Please enter device id: ")
    kr.set_password("Tuya", "device_id", DEVICE_ID)