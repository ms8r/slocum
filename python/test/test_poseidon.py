import unittest

import numpy as np

from sl import poseidon

import xray


def test_forecast():
    ds = xray.Dataset()
    ds['longitude'] = ('longitude', np.arange(-180., 180.))
    ds['latitude'] = ('latitude', np.arange(-90., 90.))
    u, v = np.meshgrid(np.arange(-90., 90.), np.arange(-180., 180.))
    u = np.array([u] * 65)
    v = np.array([v] * 65)
    time = xray.Dataset()
    time['time'] = ('time', np.linspace(0, 192, 65),
                    {'units': 'hours since 2014-03-28'})
    ds['time'] = xray.conventions.decode_cf_variable(time['time'])
    ds['uwnd'] = (['time', 'longitude', 'latitude'], u)
    ds['vwnd'] = (['time', 'longitude', 'latitude'], v)
    return ds


class PoseidonTest(unittest.TestCase):

    def test_latitude_slicer(self):

        queries = [((10., -10.), 1.9, np.linspace(10., -10., 11)),
                   ((10., -10.), 2.1, np.linspace(10., -10., 11)),
                   ((30., 10.), 0.5, np.linspace(30., 10., 41)),
                   ((-10., -30.), 0.5, np.linspace(-10., -30., 41)),
                   ((10., -10.), 2.0, np.linspace(10., -10., 11)),]

        for (north, south), delta, expected in queries:
            query = {'domain': {'N': north, 'S': south,
                                'E': -150, 'W': -170},
                 'grid_delta': (delta, 0.5)}

            lats = np.linspace(-90, 90., 361)
            slicer = poseidon.latitude_slicer(lats, query)
            np.testing.assert_array_equal(expected, lats[slicer])

            lats = np.linspace(90, -90., 361)
            slicer = poseidon.latitude_slicer(lats, query)
            np.testing.assert_array_equal(expected, lats[slicer])

        lats = np.linspace(-90, 90, 361)
        # add an irregularly spaced grid
        lats[180] = 1.1
        self.assertRaises(Exception,
                          lambda: poseidon.latitude_slicer(lats, query))

    def test_longitude_slicer(self):

        queries = [((10., 30.), 0.5, np.linspace(10., 30., 41)),
                   ((10., 30.), 1.0, np.linspace(10., 30., 21)),
                   ((170., -170.), 0.5, np.linspace(170., 190., 41)),
                   ((170., -170.), 1.1, np.linspace(170., 190., 21)),
                   ]

        for (west, east), delta, expected in queries:
            query = {'domain': {'N': 10., 'S': -10.,
                                'E': east, 'W': west},
                 'grid_delta': (0.5, delta)}

            lons = np.linspace(0., 360., 721)
            slicer = poseidon.longitude_slicer(lons, query)
            np.testing.assert_array_equal(expected, lons[slicer])

        lons = np.linspace(0., 360., 721)
        # add an irregularly spaced grid
        lons[180] = 1.1
        self.assertRaises(Exception,
                          lambda: poseidon.longitude_slicer(lons, query))

        lons = np.linspace(0., 360., 721)
        query = {'domain': {'N': 10., 'S': -10.,
                            'E': 10., 'W': -10.},
                 'grid_delta': (0.5, 0.5)}

        self.assertRaises(Exception,
                          lambda: poseidon.longitude_slicer(lons, query))

    def test_time_slicer(self):

        queries = [(np.array([0., 24, 48]))
                   ]

        time = xray.Dataset()
        time['time'] = (('time', [0, 6, 12, 18, 24, 36, 48, 72, 96],
                        {'units': 'hours since 2011-01-01'}))
        time = xray.conventions.decode_cf_variable(time['time'])

        for hours in queries:
            query = {'hours': hours}
            max_hours = int(max(hours))
            slicer = poseidon.time_slicer(time, query)
            actual = time.values[slicer][-1] - time.values[slicer][0]
            expected = np.timedelta64(max_hours, 'h')
            self.assertEqual(actual, expected)

    def test_subset(self):
        query = {'hours': np.array([0., 24, 48, 96]),
                 'domain': {'N': 10., 'S': -10.,
                            'E': 10., 'W': -10.},
                 'grid_delta': (0.5, 0.5)}

        fcst = test_forecast()
        subset = poseidon.subset(fcst, query)
        np.testing.assert_array_equal(subset['longitude'].values,
                                      np.arange(-10., 11.))
        np.testing.assert_array_equal(subset['latitude'].values,
                                      -np.arange(-10., 11.))

    def test_spot_forecast(self):

        query = {'location': {'latitude': -20., 'longitude': -154.},
                   'model': 'gfs',
                   'type': 'spot',
                   'hours': np.linspace(0, 96, 33).astype('int'),
                   'vars': ['wind'],
                   'warnings': []}

        poseidon.gfs = lambda x: test_forecast()
        fcst = poseidon.spot_forecast(query)
        np.testing.assert_array_equal(fcst['vwnd'].values, -154.)
        np.testing.assert_array_equal(fcst['uwnd'].values, -20.)

        query = {'location': {'latitude': -20.3, 'longitude': -154.7},
                   'model': 'gfs',
                   'type': 'spot',
                   'hours': np.linspace(0, 96, 33).astype('int'),
                   'vars': ['wind'],
                   'warnings': []}

        poseidon.gfs = lambda x: test_forecast()
        fcst = poseidon.spot_forecast(query)
        np.testing.assert_array_equal(fcst['vwnd'].values, -154.7)
        np.testing.assert_array_equal(fcst['uwnd'].values, -20.3)

if __name__ == "__main__":
    unittest.main()
