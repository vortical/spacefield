
import uvicorn

from typing import Union
from fastapi import FastAPI
from spacefield.resources import ephemerids, solar_system
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

origins = [
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["*"],
)
app.include_router(ephemerids.router)
app.include_router(solar_system.router)

@app.get("/")
async def read_root():
    return {"Hello": "World"}


# // to run standalone, we create our own wsgi server
if __name__ == '__main__':
    port = 8001
    uvicorn.run(app, host="0.0.0.0", port=port)
    print(f'Serving on port {port}...')
