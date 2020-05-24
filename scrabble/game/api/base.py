from dataclasses import dataclass


@dataclass
class Event:
    timestamp: int
    params: object
