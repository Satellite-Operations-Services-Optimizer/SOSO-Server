from skyfield.api import load
import os

EARTH_RADIUS = 6378.137

_de421_bsp = None
def get_ephemeris():
    global _de421_bsp
    if _de421_bsp is None:
        # Get the directory of the current file
        dir_path = os.path.dirname(os.path.realpath(__file__))
        # Construct the path to the de421.bsp file
        bsp_path = os.path.join(dir_path, 'de421.bsp')
        _de421_bsp = load(bsp_path)
    return _de421_bsp