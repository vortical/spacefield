from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional

from model.bodies import Axis


class OrientationProvider(ABC):
    @abstractmethod
    def get_axis_at_time(self, name, time: datetime) -> Optional[Axis]:
        pass

