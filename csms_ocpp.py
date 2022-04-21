import asyncio
import logging
import websockets

import settings
from charge_point_handler import ChargePointHandler

logging.basicConfig(level=logging.INFO)


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
    charge_point = ChargePointHandler(charge_point_id, websocket)

    try:
        await asyncio.gather(
            charge_point.start(),
            charge_point.wait_for_command()
        )
    except websockets.exceptions.ConnectionClosedOK:
        logging.info("Client just disconnected")
    finally:
        await websocket.close()


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
