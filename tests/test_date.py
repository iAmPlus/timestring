import os
import time
import unittest
from datetime import datetime, timedelta

from ddt import ddt
from freezegun import freeze_time

from timestring import Date, TimestringInvalid
from timestring.Date import Specified, DAYTIMES


@freeze_time('2017-06-16 19:37:22')
@ddt
class T(unittest.TestCase):
    def assert_date(self, date_str, expected_dt: datetime,
                    expected_specified=None, **kw):
        _date = Date(date_str, **kw)

        self.assertEqual(_date,
                         expected_dt,
                         '\n     Now: %s' % str(datetime.now())
                         + '\n    Text: %s' % date_str
                         + '\nExpected: %s' % str(expected_dt)
                         + '\n  Actual: %s' % str(_date))
        if expected_specified is not None:
            self.assertEqual(_date.specified, expected_specified)

    def test_date_formats(self):
        for date_str in [
            'September 5, 2012',
            '2012 5 September',
            'sep 5 2012',
            'sept 5 2012',
            "sep 5th, '12",
            '5th September, 2012',
            '2012/9/5',
            '2012-09-5T',
            '9/5/2012',
            '5th September, 2012',
            '09/05/2012',
            '5th of September, 2012',
        ]:
            self.assert_date(date_str, datetime(2012, 9, 5),
                             Specified(is_year=1, is_month=1, is_day=1))

        self.assert_date('2012', datetime(2012, 1, 1),
                         Specified(is_year=1))
        self.assert_date('January 2013', datetime(2013, 1, 1),
                         Specified(is_year=1, is_month=1))
        self.assert_date('feb 2011', datetime(2011, 2, 1),
                         Specified(is_year=1, is_month=1))
        self.assert_date('today', datetime(2017, 6, 16),
                         Specified(is_day=1))
        # TODO: 13/5/2012

    def test_time_formats(self):
        expected_datetime = datetime(2017, 6, 17, 11, 0, 0)
        for time_str in ['11am', '11 AM', '11a',]:
            self.assert_date(time_str, expected_datetime,
                             Specified(is_daytime=1, is_hour=1))
        for time_str in ["11 o'clock", '11 oclock',]:
            self.assert_date(time_str, expected_datetime,
                             Specified(is_hour=1))
            # TODO: at 11
            # TODO: eleven o'clock
            # TODO: 1100 hours

    def test_date_and_time_formats(self):
        for date_str in ['sep 5 @ 11am', 'sep 5 @ 11am', '11am, sep 5']:
            # TODO sep 5 11pm
            # TODO sep 5, 11pm
            self.assert_date(date_str, datetime(2017, 9, 5, 11, 0, 0),
                             Specified(is_month=1, is_day=1, is_daytime=1, is_hour=1))

        for date_str in [
            '09/05/2012 at 7:35pm'
            'Sep 5th, 2012 at 7:35 pm'
            '2012 sep 5 7:35PM'
            '7:35 pm on sept 5 2012'
            '2012-09-05T19:35:00'
            'September 5th, 2012 7:35 PM'
            'September 5, 2012 7:35 pm',
            'September 5th, 2012 at 7:35pm'
            '5th of September, 2012 at 7:35pm'
            '9-5-12 7:35 pm'
            "sep 5th '12 at 7:35:00 am"
        ]:
            self.assert_date(date_str, datetime(2012, 9, 5, 19, 35, 0),
                             Specified.all(is_second=0, is_microsecond=0))

        # Offset timezone
        d = Date('2014-03-06 15:33:43.764419-05')
        self.assertEqual(d.hour, 20)
        self.assertEqual(d.specified, Specified(1, 1, 1, 1, 1, 1, 1, 1))

    def test_implicit(self):
        self.assert_date('2011 nov 11 at 11:11:11',
                         datetime(2011, 11, 11, 11, 11, 11),
                         Specified.all(is_daytime=0, is_microsecond=0))

        self.assert_date('2011 nov 11 at 11:11',
                         datetime(2011, 11, 11, 11, 11,  0),
                         Specified.all(is_daytime=0, is_second=0, is_microsecond=0))

        self.assert_date('2011 nov 11 at 11am',
                         datetime(2011, 11, 11, 11,  0,  0),
                         Specified.all(is_minute=0, is_second=0, is_microsecond=0))

        self.assert_date('2011 nov 11',
                         datetime(2011, 11, 11,  0,  0,  0),
                         Specified(is_year=1, is_month=1, is_day=1))

        self.assert_date('2011 nov',
                         datetime(2011, 11,  1,  0,  0,  0),
                         Specified(is_year=1, is_month=1))

        self.assert_date('2011',
                         datetime(2011,  1,  1,  0,  0,  0),
                         Specified(is_year=1))

        self.assert_date('nov 11 at 11:11:11',
                         datetime(2017, 11, 11, 11, 11, 11),
                         Specified.all(is_year=0, is_daytime=0, is_microsecond=0))

        self.assert_date('nov 11 at 11:11',
                         datetime(2017, 11, 11, 11, 11,  0),
                         Specified(is_month=1, is_day=1, is_hour=1, is_minute=1))

        self.assert_date('nov 11 at 11am',
                         datetime(2017, 11, 11, 11,  0,  0),
                         Specified(is_month=1, is_day=1, is_daytime=1, is_hour=1))

        self.assert_date('nov 11',
                         datetime(2017, 11, 11,  0,  0,  0),
                         Specified(is_month=1, is_day=1))

        self.assert_date('nov',
                         datetime(2017, 11,  1,  0,  0,  0),
                         Specified(is_month=1))

        self.assert_date('11:11:11',
                         datetime(2017,  6,  17, 11, 11, 11),
                         Specified(is_hour=1, is_minute=1, is_second=1))

        self.assert_date('11:11',
                         datetime(2017,  6,  17, 11, 11,  0),
                         Specified(is_hour=1, is_minute=1))

        self.assert_date('11am',
                         datetime(2017,  6,  17, 11,  0,  0),
                         Specified(is_daytime=1, is_hour=1))

        self.assert_date("11 o'clock",
                         datetime(2017, 6, 17, 11, 0, 0),
                         Specified(is_hour=1)
                         )

        self.assert_date('morning',
                         datetime(2017, 6, 16, DAYTIMES['morning'], 0, 0),
                         Specified(is_daytime=1))

    def test_exceptions(self):
        for x in ['yestserday', 'Satruday', Exception]:
            with self.assertRaises(TimestringInvalid):
                Date(x)

    def test_weekdays(self):
        now = datetime.now()
        for i, day in enumerate(('monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday')):
            d = Date(day)
            self.assertLess(d.date - now, timedelta(7), day)
            self.assertEqual(d.weekday, i, day)
            self.assertEqual(d.isoweekday, 1 + i, day)
            self.assertEqual(d.specified, Specified(is_day=1))

    def test_offset(self):
        self.assert_date(
            'now',
            datetime(2017, 6, 16, 19, 3, 22),
            Specified.all(),
            offset=dict(minute=3)
        )
        self.assert_date(
            'today',
            datetime(2017, 6, 5, 4, 3, 2, 1),
            Specified(is_day=1),
            offset=dict(day=5, hour=4, minute=3, second=2, microsecond=1)
        )
        self.assert_date(
            'yesterday',
            datetime(2017, 6, 1, 2, 3, 4, 5),
            Specified(is_day=1),
            offset=dict(day=1, hour=2, minute=3, second=4, microsecond=5)
        )
        self.assertEqual(Date('august 25th 7:30am', offset=dict(hour=10)).hour, 7)

    def test_tz(self):
        self.assertEqual(Date('today', tz='US/Central').tz.zone, 'US/Central')

    def test_plus(self):
        date_1 = Date('jan 10')
        date_1.microsecond = 1
        date_2 = Date('jan 11')
        date_2.microsecond = 1
        date_3 = date_1 + '1 day'
        self.assertEqual(date_3, date_2)
        self.assertEqual(date_3.specified, Specified(is_month=1, is_day=1),
                         date_3.specified)

        date1 = Date('october 18, 2013 10:04:32 PM')
        date2 = date1 + '10 seconds'
        self.assertEqual(date1.second + 10, date2.second)
        self.assertEqual(date2.specified, Specified.all(is_microsecond=0))

    def test_minus(self):
        date_1 = Date('jan 10')
        date_1.microsecond = 1
        date_2 = Date('jan 5')
        date_2.microsecond = 1
        date_3 = Date(date_1) - '5 days'
        self.assertEqual(date_3, date_2)
        self.assertEqual(date_3.specified, Specified(is_month=1, is_day=1))

    def test_adjustment(self):
        d = Date('Jan 1st 2014 at 10 am')
        self.assert_date(d, datetime(2014, 1, 1, 10))

        d.hour = 5
        d.day = 15
        d.month = 4
        d.year = 2013
        d.minute = 40
        d.second = 14
        d.microsecond = 10001
        self.assertEqual(d, datetime(2013, 4, 15, 5, 40, 14, 10001))

        self.assertEqual(str(d.date), '2013-04-15 05:40:14.010001')

    def test_next_prev(self):
        # Month

        self.assert_date('feb', datetime(2018, 2, 1))
        self.assert_date('this feb', datetime(2018, 2, 1), )
        self.assert_date('last feb', datetime(2017, 2, 1))
        self.assert_date('previous feb', datetime(2017, 2, 1))
        self.assert_date('next feb', datetime(2018, 2, 1))
        self.assert_date('upcoming feb', datetime(2018, 2, 1))

        self.assert_date('nov', datetime(2017, 11, 1))
        self.assert_date('this nov', datetime(2017, 11, 1))
        self.assert_date('last nov', datetime(2016, 11, 1))
        self.assert_date('previous nov', datetime(2016, 11, 1))
        self.assert_date('next nov', datetime(2017, 11, 1))
        self.assert_date('upcoming nov', datetime(2017, 11, 1))

        self.assert_date('june', datetime(2017, 6, 1))
        self.assert_date('this june', datetime(2017, 6, 1))
        self.assert_date('last june', datetime(2016, 6, 1))
        self.assert_date('next june', datetime(2018, 6, 1))

        # Weekday

        self.assert_date('sun', datetime(2017, 6, 18))
        self.assert_date('this sun', datetime(2017, 6, 18))
        self.assert_date('last sun', datetime(2017, 6, 11))
        self.assert_date('previous sun', datetime(2017, 6, 11))
        self.assert_date('next sun', datetime(2017, 6, 18))
        self.assert_date('upcoming sun', datetime(2017, 6, 18))

        self.assert_date('wed', datetime(2017, 6, 21))
        self.assert_date('last wed', datetime(2017, 6, 14))
        self.assert_date('previous wed', datetime(2017, 6, 14))
        self.assert_date('next wed', datetime(2017, 6, 21))
        self.assert_date('upcoming wed', datetime(2017, 6, 21))

        self.assert_date('fri', datetime(2017, 6, 23))
        self.assert_date('this fri', datetime(2017, 6, 23))
        self.assert_date('last fri', datetime(2017, 6, 9))
        self.assert_date('next fri', datetime(2017, 6, 23))

    def test_ago(self):
        self.assert_date('2 years ago', datetime(2015, 6, 16, 19, 37, 22))
        self.assert_date('2 months ago', datetime(2017, 4, 16, 19, 37, 22))
        self.assert_date('2 weeks ago', datetime(2017, 6, 2, 19, 37, 22))
        self.assert_date('2 days ago', datetime(2017, 6, 14, 19, 37, 22))
        self.assert_date('2 hours ago', datetime(2017, 6, 16, 17, 37, 22))
        self.assert_date('2 minutes ago', datetime(2017, 6, 16, 19, 35, 22))
        self.assert_date('2 seconds ago', datetime(2017, 6, 16, 19, 37, 20))

        # Implicit change of year, month, date etc
        self.assert_date('10 months ago', datetime(2016, 4, 16, 19, 37, 22))
        self.assert_date('20 days ago', datetime(2017, 5, 27, 19, 37, 22))
        self.assert_date('20 hours ago', datetime(2017, 6, 15, 23, 37, 22))
        self.assert_date('45 minutes ago', datetime(2017, 6, 16, 18, 52, 22))
        self.assert_date('45 seconds ago', datetime(2017, 6, 16, 19, 36, 37))

    def test_from_now(self):
        self.assert_date('2 years from now', datetime(2019, 6, 16, 19, 37, 22))
        self.assert_date('2 months from now', datetime(2017, 8, 16, 19, 37, 22))
        self.assert_date('2 weeks from now', datetime(2017, 6, 30, 19, 37, 22))
        self.assert_date('2 days from now', datetime(2017, 6, 18, 19, 37, 22))
        self.assert_date('2 hours from now', datetime(2017, 6, 16, 21, 37, 22))
        self.assert_date('2 minutes from now', datetime(2017, 6, 16, 19, 39, 22))
        self.assert_date('2 seconds from now', datetime(2017, 6, 16, 19, 37, 24))

        # Implicit change of year, month, date etc
        self.assert_date('10 months from now', datetime(2018, 4, 16, 19, 37, 22))
        self.assert_date('20 days from now', datetime(2017, 7, 6, 19, 37, 22))
        self.assert_date('20 hours from now', datetime(2017, 6, 17, 15, 37, 22))
        self.assert_date('45 minutes from now', datetime(2017, 6, 16, 20, 22, 22))
        self.assert_date('45 seconds from now', datetime(2017, 6, 16, 19, 38, 7))

    def test_in(self):  # Same as 'from now'
        self.assert_date('in 2 years', datetime(2019, 6, 16, 19, 37, 22))
        self.assert_date('in 2 months', datetime(2017, 8, 16, 19, 37, 22))
        self.assert_date('in 2 weeks', datetime(2017, 6, 30, 19, 37, 22))
        self.assert_date('in 2 days', datetime(2017, 6, 18, 19, 37, 22))
        self.assert_date('in 2 hours', datetime(2017, 6, 16, 21, 37, 22))
        self.assert_date('in 2 minutes', datetime(2017, 6, 16, 19, 39, 22))
        self.assert_date('in 2 seconds', datetime(2017, 6, 16, 19, 37, 24))

        # Implicit change of year, month, date etc
        self.assert_date('in 10 months', datetime(2018, 4, 16, 19, 37, 22))
        self.assert_date('in 20 days', datetime(2017, 7, 6, 19, 37, 22))
        self.assert_date('in 20 hours', datetime(2017, 6, 17, 15, 37, 22))
        self.assert_date('in 45 minutes', datetime(2017, 6, 16, 20, 22, 22))
        self.assert_date('in 45 seconds', datetime(2017, 6, 16, 19, 38, 7))


def main():
    os.environ['TZ'] = 'UTC'
    time.tzset()
    unittest.main()


if __name__ == '__main__':
    main()
