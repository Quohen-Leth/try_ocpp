import logging

import uvicorn
from fastapi import FastAPI, Request, WebSocket

import settings
from charge_point_handler import ChargePointHandler
from central_system_handler import central_system

# TODO: differentiate websocket server and http server with FastAPI background tasks

app = FastAPI()
logging.basicConfig(level=logging.INFO)


class SocketAdapter:
    """ Mapper between FastAPI WebSocket and websockets lib."""
    def __init__(self, websocket: WebSocket):
        self._ws = websocket

    async def recv(self):
        return await self._ws.receive_text()

    async def send(self, msg):
        await self._ws.send_text(msg)


@app.websocket("/{charge_point_id}")
async def websocket_endpoint(
        websocket: WebSocket,
        charge_point_id: str,
):
    await websocket.accept(subprotocol=settings.PROTOCOL)
    charge_point = ChargePointHandler(charge_point_id, SocketAdapter(websocket))
    logging.info(f"Charging station {charge_point.id} connected.")
    queue = central_system.register_charger(charge_point)
    await queue.get()


@app.get("/")
async def view_chargers():
    response = await central_system.view_chargers()
    return {"Connected Charging Stations": response}


@app.post("/base-report")
async def get_base_report(request: Request):
    data = await request.json()
    return await central_system.get_base_report(data["cp_id"])


@app.post("/start-transaction")
async def start_transaction(request: Request):
    data = await request.json()
    return await central_system.start_transaction(data["cp_id"])


@app.post("/stop-transaction")
async def stop_transaction(request: Request):
    data = await request.json()
    return await central_system.stop_transaction(data["cp_id"])


if __name__ == '__main__':
    uvicorn.run("csms_fastapi:app", host=settings.HOST, port=settings.PORT, reload=True)
