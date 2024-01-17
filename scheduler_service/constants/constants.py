from skyfield.api import load

EARTH_RADIUS = 6371

_de421_bsp = None
def get_ephemeris():
    global _de421_bsp
    if _de421_bsp is None:
        _de421_bsp = load('./de421.bsp')
    return _de421_bsp