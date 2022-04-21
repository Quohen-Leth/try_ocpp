import asyncio
import logging
import uuid
from datetime import datetime

from ocpp.routing import on
from ocpp.v20 import call, call_result, ChargePoint

from io_handler import connect_stdin_stdout

logging.basicConfig(level=logging.INFO)


class ChargePointHandler(ChargePoint):
    @on("Authorize")
    async def on_authorize(self, **kwargs):
        logging.info("Authorization")
        return call_result.AuthorizePayload(
            id_token_info={
                "status": "Accepted"
            },
            certificate_status=None,
            evse_id=None,
        )

    @on("GetBaseReport")
    async def on_get_base_report(self, **kwargs):
        logging.info("Base report")
        return call_result.GetBaseReportPayload(
            status="Accepted"
        )

    @on("GetReport")
    async def on_get_report(self, **kwargs):
        logging.info("Report")
        return call_result.GetReportPayload(
            status="Accepted"
        )

    @on("BootNotification")
    async def on_boot_notification(self, charging_station, reason, **kwargs):
        return call_result.BootNotificationPayload(
            current_time=datetime.utcnow().isoformat(),
            interval=10,
            status="Accepted"
        )

    @on("Heartbeat")
    async def on_heartbeat(self):
        logging.info("Got a heartbeat")
        return call_result.HeartbeatPayload(
            current_time=f"{datetime.utcnow():%Y-%m-%dT%H:%M:%S}Z"
        )

    @on("TransactionEvent")
    async def on_transaction_event(self, **kwargs):
        logging.info("Transaction event")
        return call_result.TransactionEventPayload()

    async def send_authorization(self, **kwargs):
        request = call.AuthorizePayload(
            id_token={
                "idToken": str(uuid.uuid4()),
                "type": "Local"
            },
            _15118_certificate_hash_data=None,
            evse_id=None,
        )
        await self.call(request)

    async def send_get_base_report(self, **kwargs):
        request = call.GetBaseReportPayload(
            request_id=111,
            report_base="SummaryInventory"
        )
        await self.call(request)

    async def send_report(self):
        request = call.GetReportPayload()
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
            logging.info("Connected to central system.")
            await self.send_heartbeat(response.interval)

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
                "id": str(uuid.uuid4())
            },
        )
        await self.call(request)

    async def wait_for_command(self):
        reader, writer = await connect_stdin_stdout()
        while True:
            res = await reader.readline()
            res_str = res.decode().strip()
            if not res:
                break
            if res_str == "st":
                await self.send_transaction_started()
            elif res_str == "br":
                await self.send_get_base_report()
            elif res_str == "au":
                await self.send_authorization()
            elif res_str == "rr":
                await self.send_report()
