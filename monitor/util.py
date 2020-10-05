from datetime import datetime

import click


def console_log(msg: str, color: str = "green"):
    click.echo(
        click.style(f'[{datetime.now().strftime("%d/%m/%Y %H:%M:%S")}] {msg}', fg=color)
    )
