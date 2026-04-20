import os
from dotenv import load_dotenv

load_dotenv()

DATA_DIRECTORY = os.getenv("DATA_PATH", "/spacefield/data")
GM_KERNEL_PATH = os.path.join(DATA_DIRECTORY, "gm_de440.tpc")
SPACECRAFT_REGISTRY_PATH = os.path.join(DATA_DIRECTORY, "spacecraft_registry.json")
BURNS_DIRECTORY = os.path.join(DATA_DIRECTORY, "burns")
TRAJECTORY_DIRECTORY = os.path.join(DATA_DIRECTORY, "trajectories")
