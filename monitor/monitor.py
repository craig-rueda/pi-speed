from json import dumps, loads
import re
import ssl
import threading
import time
import traceback

from monitor.output.base import ConsoleOutputDevice
from monitor.output.oled import RpiOled
from monitor.util import console_log
import requests
from websocket import WebSocketApp

MESSAGE_SIZE_RE = re.compile("^([0-9]+)\n(.*)", re.S)
ADDRESS_RE = re.compile("([^/]+)")
KbPS = float(1000)
MbPS = float(KbPS ** 2)  # 1,000,000
GbPS = float(KbPS ** 3)  # 1,000,000,000
RESTART_INT_SECS = 600  # Restart every 10min


class InvalidLoginException(Exception):
    pass


class Monitor:
    def __init__(
        self,
        router_url: str,
        monitor_if: str,
        username: str,
        password: str,
        console_only: bool = False,
    ) -> None:
        self._router_url = router_url
        self._username = username
        self._password = password
        self._monitor_if = monitor_if
        self._display = ConsoleOutputDevice() if console_only else RpiOled()
        self._session_id = ""
        self._ws: WebSocketApp = None
        self._remaining_bytes = 0
        self._partial_message = ""

        # The API only allows us to receive messages for 20min at a time,
        # so this thread will periodically restart the connection
        self._monitor_thread = threading.Thread(target=self._monitor_run)
        self._monitor_thread.setDaemon(True)
        self._worker_thread = None

    def _monitor_run(self):
        while True:
            if self._worker_thread and self._worker_thread.is_alive():
                console_log("Closing websocket", color="yellow")
                self._ws.close()
                self._worker_thread.join(60)

            self._session_id = ""
            self._ws: WebSocketApp = None
            self._remaining_bytes = 0
            self._partial_message = ""

            self._worker_thread = threading.Thread(target=self._do_login_and_connect)
            self._worker_thread.setDaemon(True)
            self._worker_thread.start()

            time.sleep(RESTART_INT_SECS)

    def on_ws_message(self, message: str):
        if self._remaining_bytes:
            curr_msg, message = self._gobble_bytes(self._remaining_bytes, message)
            self._partial_message += curr_msg
            self._remaining_bytes -= len(curr_msg)

        if self._remaining_bytes < 0:
            # Something's not right here. Just reset...
            self.login_and_connect()
        elif self._remaining_bytes == 0:
            if self._partial_message:
                msg_to_handle = self._partial_message
                self._partial_message = ""
                self._handle_message(msg_to_handle)

            m = MESSAGE_SIZE_RE.match(message)
            while m:
                msg_len = int(m.group(1))
                curr_msg, message = self._gobble_bytes(msg_len, m.group(2))

                if len(curr_msg) == msg_len:
                    self._handle_message(curr_msg)
                else:
                    self._partial_message = curr_msg
                    self._remaining_bytes = msg_len - len(curr_msg)

                m = MESSAGE_SIZE_RE.match(message) if message else None

    def _gobble_bytes(self, cnt: int, data: str):
        if len(data) >= cnt:
            gobbled = data[:cnt]
            remaining = data[cnt:]
        else:
            gobbled = data
            remaining = ""

        return gobbled, remaining

    def _handle_message(self, message: str):
        data = loads(message)
        interfaces = data.get("interfaces")

        if interfaces:
            interface = interfaces[self._monitor_if]
            stats = interface["stats"]
            rx_bps = int(stats["rx_bps"]) * 8
            tx_bps = int(stats["tx_bps"]) * 8

            if_addr_match = ADDRESS_RE.match(interface["addresses"][0])
            if_addr = if_addr_match.group(1) if if_addr_match else "n/a"

            self._update_output(rx_bps, tx_bps, if_addr)

    def _update_output(self, rx_bps: int, tx_bps: int, address: str):
        self._display.update_display(
            [
                f"IP: {address}",
                f"Up: {self._human_bps(tx_bps)}",
                f"Dn: {self._human_bps(rx_bps)}",
            ]
        )

    @staticmethod
    def _human_bps(bps: int):
        if bps < KbPS:
            return "{0} bps".format(bps)
        elif KbPS <= bps < MbPS:
            return "{0:.1f} Kbps".format(bps / KbPS)
        elif MbPS <= bps < GbPS:
            return "{0:.1f} Mbps".format(bps / MbPS)
        else:
            return "{0:.1f} Gbps".format(bps / GbPS)

    def on_ws_error(self, ws, error):
        print(error)

    def on_ws_open(self):
        console_log("Connection opened.")
        subscribe_data = dumps(
            {
                "SUBSCRIBE": [{"name": "interfaces"}, {"name": "system-stats"}],
                "UNSUBSCRIBE": [],
                "SESSION_ID": self._session_id,
            }
        )
        subscribe_frame = f"{len(subscribe_data)}\n{subscribe_data}"
        self._ws.send(subscribe_frame)
        console_log("Subscribed.")

    def on_ws_close(self, ws):
        console_log("Connection closed. Reconnecting...", color="red")
        self.login_and_connect()

    def login_and_connect(self):
        self._monitor_thread.start()
        self._monitor_thread.join()

    def _do_login_and_connect(self):
        self._keepalive = True

        console_log(f"Connecting to {self._router_url}...")

        try:
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
        except Exception:
            console_log(traceback.format_exc(), color="red")
