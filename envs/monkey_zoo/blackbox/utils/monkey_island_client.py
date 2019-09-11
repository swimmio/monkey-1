import json
from time import sleep

import requests

# SHA3-512 of '1234567890!@#$%^&*()_nothing_up_my_sleeve_1234567890!@#$%^&*()'
NO_AUTH_CREDS = '55e97c9dcfd22b8079189ddaeea9bce8125887e3237b800c6176c9afa80d2062' \
                '8d2c8d0b1538d2208c1444ac66535b764a3d902b35e751df3faec1e477ed3557'
SLEEP_BETWEEN_REQUESTS_SECONDS = 0.5


def avoid_race_condition(func):
    sleep(SLEEP_BETWEEN_REQUESTS_SECONDS)
    return func


class MonkeyIslandClient(object):
    def __init__(self, server_address):
        self.addr = "https://{IP}/".format(IP=server_address)
        self.token = self.try_get_jwt_from_server()

    def try_get_jwt_from_server(self):
        try:
            return self.get_jwt_from_server()
        except requests.ConnectionError:
            print("Unable to connect to island, aborting!")
            assert False

    def get_jwt_from_server(self):
        resp = requests.post(self.addr + "api/auth",
                             json={"username": NO_AUTH_CREDS, "password": NO_AUTH_CREDS},
                             verify=False)
        return resp.json()["access_token"]

    def request_get(self, url, data=None):
        return requests.get(self.addr + url,
                            headers={"Authorization": "JWT " + self.token},
                            params=data,
                            verify=False)

    def request_post(self, url, data):
        return requests.post(self.addr + url,
                             data=data,
                             headers={"Authorization": "JWT " + self.token},
                             verify=False)

    def request_post_json(self, url, dict_data):
        return requests.post(self.addr + url,
                             json=dict_data,
                             headers={"Authorization": "JWT " + self.token},
                             verify=False)

    def get_api_status(self):
        return self.request_get("api")

    @avoid_race_condition
    def import_config(self, config_contents):
        _ = self.request_post("api/configuration/island", data=config_contents)

    @avoid_race_condition
    def run_monkey_local(self):
        response = self.request_post_json("api/local-monkey", dict_data={"action": "run"})
        if MonkeyIslandClient.monkey_ran_successfully(response):
            print("Running the monkey.")
        else:
            print("Failed to run the monkey.")
            assert False

    @staticmethod
    def monkey_ran_successfully(response):
        return response.ok and json.loads(response.content)['is_running']

    @avoid_race_condition
    def kill_all_monkeys(self):
        if self.request_get("api", {"action": "killall"}).ok:
            print("Killing all monkeys after the test.")
        else:
            print("Failed to kill all monkeys.")
            assert False

    @avoid_race_condition
    def reset_env(self):
        if self.request_get("api", {"action": "reset"}).ok:
            print("Resetting environment after the test.")
        else:
            print("Failed to reset the environment.")
            assert False
