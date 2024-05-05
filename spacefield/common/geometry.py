import numpy as np
from skyfield.functions import angle_between, mxv
import math


def unit(vector):
    """
    Returns the unit vector
    """
    return vector / np.linalg.norm(vector)

def projection(u, n):
    """
    given u = v + (projection of u onto n), then
    v = u - (projection of u onto n)
    which is what we want.
    :param u: vector
    :param n: normal to plan
    :return: projection of u onto plane with normal n
    """
    #      u - (projection of u onto n)
    return u - np.dot(u,n)/np.dot(n, n) * n

def circular_angle(v1, v2, plane_normal=np.array([0,0,1])):
    """

    :param v1:
    :param v2:
    :param plane_normal:
    :return: An angle between 0 and 2PI, in the direction of the normal.
    """
    v1_p = projection(v1, plane_normal)
    v2_p = projection(v2, plane_normal)

    a = angle_between(v1_p, v2_p)

    if angle_between(np.cross(v1_p, v2_p), plane_normal) < math.pi/2:
        return a
    else:
        return math.pi * 2 - a


def to_cartesian(ra, dec, to_rad=True):
    ra = ra if not to_rad else math.radians(ra)
    dec = dec if not to_rad else math.radians(dec)
    x = math.cos(dec) * math.cos(ra)
    y = math.cos(dec) * math.sin(ra)
    z = math.sin(dec)
    return x, y, z