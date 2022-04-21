import asyncio
import logging
import websockets

import click

import settings
from charge_point_handler import ChargePointHandler

logging.basicConfig(level=logging.INFO)


async def main(station_name):
    async with websockets.connect(
        f"ws://{settings.HOST}:{settings.PORT}/{station_name}",
        subprotocols=[settings.PROTOCOL]
    ) as ws:
        charge_point = ChargePointHandler(station_name, ws)
        await asyncio.gather(
            charge_point.start(),
            charge_point.send_boot_notification(),
            charge_point.wait_for_command()
        )


@click.group()
def cli():
    pass


@cli.command()
@click.option("-n", "--station_name")
def start(station_name):
    asyncio.run(main(station_name))


if __name__ == "__main__":
    cli()
