import logging.config

import click
from monitor.monitor import Monitor

logger = logging.getLogger(__name__)


@click.group()
def monitor():
    pass


@monitor.command("start")
@click.option(
    "--router-url",
    default="https://192.168.5.1",
    prompt="Base URL of your Ubiquiti router's admin console",
)
@click.option("--interface", default="eth9", prompt="Router interface to monitor")
@click.option(
    "--username", default="ubnt", prompt="Username to login to the admin console"
)
@click.option(
    "--password", default="ubnt", prompt="Password to login to the admin console"
)
@click.option(
    "--console-only",
    "-c",
    default=False,
    is_flag=True,
    help="If set, only output to console",
)
def start(
    router_url: str, interface: str, username: str, password: str, console_only: bool
):
    m = Monitor(router_url, interface, username, password, console_only)
    m.login_and_connect()
