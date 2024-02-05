# import datetime as dt
# from pytz import timezone
# from skyfield import almanac
# from skyfield.api import N, W, wgs84, load
#
# from skyfield import api
# from skyfield.api import load
#
#
#
# ts = api.load.timescale()
#
# time = ts.now()
# print(time)
# print(time.utc_datetime())
#
# #
# # # Figure out local midnight.
# # zone = timezone('US/Eastern')
# # now = zone.localize(dt.datetime.now())
# # midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
# # next_midnight = midnight + dt.timedelta(days=1)
# #
# # ts = load.timescale()
# # t0 = ts.from_datetime(midnight)
# # t1 = ts.from_datetime(next_midnight)
# # eph = load('de421.bsp')
# # bluffton = wgs84.latlon(43.3583, -73.67384)
# # f = almanac.dark_twilight_day(eph, bluffton)
# # times, events = almanac.find_discrete(t0, t1, f)
# #
# # previous_e = f(t0).item()
# # for t, e in zip(times, events):
# #     tstr = str(t.astimezone(zone))[:16]
# #     if previous_e < e:
# #         print(tstr, ' ', almanac.TWILIGHTS[e], 'starts')
# #     else:
# #         print(tstr, ' ', almanac.TWILIGHTS[previous_e], 'ends')
# #     previous_e = e
# #
#
#
# def distance_between_moon_and_earth():
#     ts = api.load.timescale()
#
#     t1 = ts.utc(2021, 2, 26, 15, 18, 55)
#     t2 = ts.utc(2021, 2, 26, 15, 19, 55)
#
#     planets = api.load('de421.bsp')
#
#     moon = planets['moon'].at(t1)
#
#
#     v = planets['moon'].at(t1) - planets['earth'].at(t1)
#     print('The Moon is %d km away' % v.distance().km)
#
#
#     v = planets['moon'].at(t2) - planets['earth'].at(t2)
#     print('The Moon is %d km away' % v.distance().km)
#
#
#     v = planets['moon'].at(t2) - planets['moon'].at(t1)
#     print('The Moon is moved %d km away in a minute' % v.distance().km)
#
#
# distance_between_moon_and_earth()