
import uvicorn

from fastapi import FastAPI
from spacefield.resources import ephemeris
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
app.include_router(ephemeris.router)

# To run standalone we create our own wsgi server
if __name__ == '__main__':
    port = 8001
    uvicorn.run(app, host="0.0.0.0", port=port)
    print(f'Serving on port {port}...')
