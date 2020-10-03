import importlib.util
from json import dumps
import ssl

import requests
from websocket import WebSocketApp

try:
    importlib.util.find_spec("RPi.GPIO")
    import RPi.GPIO as GPIO
except ImportError:
    """
    import FakeRPi.GPIO as GPIO
    OR
    import FakeRPi.RPiO as RPiO
    """
    import FakeRPi.GPIO as GPIO


class InvalidLoginException(Exception):
    pass


class Monitor:
    def __init__(self, router_url: str, username: str, password: str) -> None:
        self._router_url = router_url
        self._username = username
        self._password = password
        self._session_id = ""
        self._ws: WebSocketApp = None

    def on_ws_message(self, message):
        print(message)

    def on_ws_error(self, ws, error):
        print(error)

    def on_ws_open(self):
        print("### opened ###")
        subscribe_data = dumps(
            {
                "SUBSCRIBE": [
                    {"name": "interfaces"},
                    {"name": "system-stats"},
                    {"name": "pon-stats"},
                ],
                "UNSUBSCRIBE": [],
                "SESSION_ID": self._session_id,
            }
        )
        subscribe_frame = f"{len(subscribe_data)}\n{subscribe_data}"
        self._ws.send(subscribe_frame)
        print("### subscribed ###")

    def on_ws_close(self, ws):
        print("### closed ###")

    def login_and_connect(self):
        r = requests.post(
            self._router_url,
            {"username": self._username, "password": self._password},
            allow_redirects=False,
            verify=False,
        )
        auth_cookies = r.cookies
        # Make sure we're actually good to go by hitting a protected URL...
        r = requests.get(
            f"{self._router_url}/api/edge/data.json?data=dhcp_leases",
            cookies=auth_cookies,
            verify=False,
        )

        if r.status_code != 200:
            # Something went wrong
            raise InvalidLoginException()

        cookie_header_str = "; ".join(
            [f"{cookie[0]}={cookie[1]}" for cookie in auth_cookies.items()]
        )
        self._session_id = auth_cookies["PHPSESSID"]
        self._ws = WebSocketApp(
            "wss://192.168.5.1/ws/stats",
            cookie=cookie_header_str,
            on_message=self.on_ws_message,
            on_error=self.on_ws_error,
            on_close=self.on_ws_close,
            on_open=self.on_ws_open,
        )
        self._ws.run_forever(
            ping_interval=10, sslopt={"cert_reqs": ssl.VerifyMode.CERT_NONE}
        )
