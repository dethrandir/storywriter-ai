# pov.py
from enum import Enum

class PovType(Enum):
    FIRST_PERSON = "first_person" # birinci sahis bakis acisi
    THIRD_PERSON_LIMITED = "third_person_limited" # ucuncu sahis bakis acisi
    THIRD_OMNISCIENT = "third_omniscient" # tanrisal bakis acisi
