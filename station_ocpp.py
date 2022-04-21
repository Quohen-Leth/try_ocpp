import asyncio
import logging
import websockets
from datetime import datetime

import click
from ocpp.v20 import call
from ocpp.v20 import ChargePoint

import settings
from io_handler import connect_stdin_stdout

logging.basicConfig(level=logging.INFO)


class LocalChargePoint(ChargePoint):
    async def send_heartbeat(self, interval):
        request = call.HeartbeatPayload()
        while True:
            await self.call(request)
            await asyncio.sleep(interval)

    async def send_transaction_started(self):
        request = call.TransactionEventPayload(
            event_type="Started",
            timestamp=f"{datetime.utcnow():%Y-%m-%dT%H:%M:%S}Z",
            trigger_reason="Authorized",
            seq_no=1,
            transaction_data={
                "id": "e7073706-4f34-4825-828d-ef07f1af9d69"
            },
        )
        await self.call(request)

    async def send_boot_notification(self):
        request = call.BootNotificationPayload(
            charging_station={
                "model": "Wallbox XYZ",
                "vendor_name": "anewone"
            },
            reason="PowerUp"
        )

        response = await self.call(request)

        if response.status == "Accepted":
            print("Connected to central system.")
            await self.send_transaction_started()
            await self.send_heartbeat(response.interval)

    async def wait_for_command(self):
        reader, writer = await connect_stdin_stdout()
        while True:
            res = await reader.readline()
            res_str = res.decode().strip()
            if not res:
                break
            if res_str == "st":
                await self.send_transaction_started()


async def main(station_name):
    async with websockets.connect(
        f"ws://{settings.HOST}:{settings.PORT}/{station_name}",
        subprotocols=[settings.PROTOCOL]
    ) as ws:
        charge_point = LocalChargePoint(station_name, ws)
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
