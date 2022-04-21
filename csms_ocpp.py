import asyncio
import logging
import websockets
from datetime import datetime

from ocpp.routing import on
from ocpp.v20 import ChargePoint as cp
from ocpp.v20 import call_result

import settings

logging.basicConfig(level=logging.INFO)


class ChargePoint(cp):
    @on("BootNotification")
    async def on_boot_notification(self, charging_station, reason, **kwargs):
        return call_result.BootNotificationPayload(
            current_time=datetime.utcnow().isoformat(),
            interval=20,
            status="Accepted"
        )

    @on("Heartbeat")
    async def on_heartbeat(self):
        print("Got a heartbeat")
        return call_result.HeartbeatPayload(
            current_time=f"{datetime.utcnow():%Y-%m-%dT%H:%M:%S}Z"
        )

    @on("TransactionEvent")
    async def on_transaction_event(self, **kwargs):
        print("Transaction event")
        return call_result.TransactionEventPayload()


async def on_connect(websocket, path):
    """ For every new charge point that connects, create a ChargePoint
    instance and start listening for messages."""
    try:
        requested_protocols = websocket.request_headers["Sec-WebSocket-Protocol"]
    except KeyError:
        logging.info("Client hasn't requested any Subprotocol. Closing Connection")
    if websocket.subprotocol:
        logging.info(f"Protocols Matched: {websocket.subprotocol}", )
    else:
        # In the websockets lib if no subprotocols are supported by the
        # client and the server, it proceeds without a subprotocol,
        # so we have to manually close the connection.
        logging.warning("Protocols Mismatched | Expected Subprotocols: %s,"
                        " but client supports %s | Closing connection",
                        websocket.available_subprotocols,
                        requested_protocols)
        return await websocket.close()

    charge_point_id = path.strip('/')
    charge_point = ChargePoint(charge_point_id, websocket)

    await charge_point.start()


async def main():
    server = await websockets.serve(
        on_connect,
        settings.HOST,
        settings.PORT,
        subprotocols=[settings.PROTOCOL]
    )
    logging.info("WebSocket Server Started listening to new connections...")
    await server.wait_closed()


if __name__ == "__main__":
    asyncio.run(main())
