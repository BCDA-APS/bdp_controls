"""
Load devices and plans for bluesky queueserver.
"""

import pathlib, sys
sys.path.append(
    str(pathlib.Path(__file__).absolute().parent.parent / "bluesky")
)
print(f"{sys.path[-1] = }")
import instrument
print(f"{instrument = }")
from instrument.collection import *
listobjects()
listplans()
