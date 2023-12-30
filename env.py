import keyring as kr
from getpass import getpass
import pathlib
# Tuya cloud configuration
ACCESS_ID = None # your_access_id
ACCESS_KEY = kr.get_password("Tuya","secret") # your_access_key
DEVICE_ID = None # your_device_id
ENDPOINT = "https://openapi.tuyaeu.com"

# csv settings
COLUMN_ORDER = ['t', 'online', 'relay_status', 'countdown_1', 'switch_1', 'cur_voltage', 'cur_current', 'cycle_time', 'cur_power', 'add_ele', 'random_time']
DATA_DIR = f"{pathlib.Path(__file__).parent.resolve()}/data" # path to data directory


if ACCESS_KEY is None or ACCESS_KEY == "":
    ACCESS_KEY = getpass("Please enter Tuya Cloud project access key (secret): ")
    kr.set_password("Tuya", "secret", ACCESS_KEY)