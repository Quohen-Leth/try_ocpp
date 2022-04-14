import asyncio
import logging
import websockets
from datetime import datetime

import click
from ocpp.v20 import call
from ocpp.v20 import ChargePoint

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


async def main():
    async with websockets.connect(
        "ws://localhost:9000/CP_1",
        subprotocols=["ocpp2.0"]
    ) as ws:
        charge_point = LocalChargePoint("CP_1", ws)
        await asyncio.gather(charge_point.start(), charge_point.send_boot_notification())


@click.group()
def cli():
    pass


@cli.command()
def start():
    asyncio.run(main())


if __name__ == "__main__":
    cli()
