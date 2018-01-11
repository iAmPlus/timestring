import os
import time
import unittest
from datetime import datetime, timedelta

from ddt import ddt
from freezegun import freeze_time

from timestring import Context, TimestringInvalid
from timestring.Date import Date
from timestring.Range import Range
from timestring import Context, WEEKEND_START_HOUR, WEEKEND_END_HOUR


@freeze_time('2017-06-16 19:37:22')
@ddt
class T(unittest.TestCase):
    def assert_range(self, range_str, expected_start: datetime,
                     expected_end: datetime,
                     start_tolerance: timedelta = timedelta(),
                     end_tolerance: timedelta = timedelta(),
                     **kw):
        start, end = Range(range_str, **kw)

        min_start = expected_start - start_tolerance
        max_start = expected_start + start_tolerance
        min_end = expected_end - end_tolerance
        max_end = expected_end + end_tolerance

        self.assertTrue(
            min_start <= start <= max_start,
            '\n         Now: %s' % datetime.now()
            + '\n          Text: "%s"' % range_str
            + '\nExpected start: %s += %s' % (expected_start, start_tolerance)
            + '\n  Actual start: %s' % start
        )
        self.assertTrue(
            min_end <= end <= max_end,
            '\n         Now: %s' % datetime.now()
            + '\n        Text: "%s"' % range_str
            + '\nExpected end: %s += %s' % (expected_end, end_tolerance)
            + '\n  Actual end: %s' % end
        )
        if start_tolerance and end_tolerance:
            self.assertEqual(expected_end - expected_start, end.date - start.date)

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
            '5th of September, 2012',
        ]:
            self.assert_range(date_str,
                              datetime(2012, 9, 5),
                              datetime(2012, 9, 6))

        # TODO: 13/5/2012

    def test_exceptions(self):
        for date_str in ['yestserday', 'Satruday', Exception]:
            with self.assertRaises(TimestringInvalid):
                Range(date_str)

    def test_explicit_end(self):
        self.assert_range('2012 feb 2 1:13PM to 6:41 am on sept 8 2012',
                          datetime(2012, 2, 2, 13, 13),
                          datetime(2012, 9, 8, 6, 41))

        self.assert_range('From 04/17/13 04:18:00 to 05/01/13 17:01:00',
                          datetime(2013, 4, 17, 4, 18),
                          datetime(2013, 5, 1, 17, 1),
                          tz='US/Central')

        self.assert_range('from jan 10 2010 5 am to jan 10, 2010 9 am',
                          datetime(2010, 1, 10, 5),
                          datetime(2010, 1, 10, 9))

        self.assert_range('from january 10th 2010 to jan 12th 2010',
                          datetime(2010, 1, 10),
                          datetime(2010, 1, 12))

    def test_implicit(self):
        self.assert_range('2011 nov 11 at 11:11:11',
                          datetime(2011, 11, 11, 11, 11, 11),
                          datetime(2011, 11, 11, 11, 11, 12))

        self.assert_range('2011 nov 11 at 11:11',
                          datetime(2011, 11, 11, 11, 11,  0),
                          datetime(2011, 11, 11, 11, 12,  0))

        self.assert_range('2011 nov 11 at 11am',
                          datetime(2011, 11, 11, 11,  0,  0),
                          datetime(2011, 11, 11, 12,  0,  0))

        self.assert_range('2011 nov 11',
                          datetime(2011, 11, 11,  0,  0,  0),
                          datetime(2011, 11, 12,  0,  0,  0))

        self.assert_range('2011 nov',
                          datetime(2011, 11,  1,  0,  0,  0),
                          datetime(2011, 12,  1,  0,  0,  0))

        self.assert_range('2011',
                          datetime(2011,  1,  1,  0,  0,  0),
                          datetime(2012,  1,  1,  0,  0,  0))

        self.assert_range('nov 11 at 11:11:11',
                          datetime(2017, 11, 11, 11, 11, 11),
                          datetime(2017, 11, 11, 11, 11, 12))

        self.assert_range('nov 11 at 11:11',
                          datetime(2017, 11, 11, 11, 11,  0),
                          datetime(2017, 11, 11, 11, 12,  0))

        self.assert_range('nov 11 at 11am',
                          datetime(2017, 11, 11, 11,  0,  0),
                          datetime(2017, 11, 11, 12,  0,  0))

        self.assert_range('nov 11',
                          datetime(2017, 11, 11,  0,  0,  0),
                          datetime(2017, 11, 12,  0,  0,  0))

        self.assert_range('nov',
                          datetime(2017, 11,  1,  0,  0,  0),
                          datetime(2017, 12,  1,  0,  0,  0))

        self.assert_range('11:11:11',
                          datetime(2017,  6,  16, 11, 11, 11),
                          datetime(2017,  6,  16, 11, 11, 12))

        self.assert_range('11:11',
                          datetime(2017,  6,  16, 11, 11,  0),
                          datetime(2017,  6,  16, 11, 12,  0))

        self.assert_range('11am',
                          datetime(2017,  6,  16, 11,  0,  0),
                          datetime(2017,  6,  16, 12,  0,  0))

        self.assert_range('january 10 to jan 12',
                          datetime(2018, 1, 10),
                          datetime(2018, 1, 12))

        self.assert_range('between january 10 and jan 12',
                          datetime(2018, 1, 10),
                          datetime(2018, 1, 12))

        self.assert_range('10am to 11pm',
                          datetime(2017, 6, 17, 10),
                          datetime(2017, 6, 17, 23))

        self.assert_range('10pm to 11am',
                          datetime(2017, 6, 16, 22),
                          datetime(2017, 6, 17, 11))

    def test_implicit_end(self):
        self.assert_range('tomorrow 10am to 5pm',
                          datetime(2017, 6, 17, 10),
                          datetime(2017, 6, 17, 17))

        # TODO: from jan 10th 2010 to jan 11
        # TODO: jan 10 from 5 to 9 am
        # TODO: from jan 10th 10am to 11am
        # TODO: jan 10th from 10am to 11am
        # TODO: from jan to feb 2010
        # TODO: jan to feb 2010
        # TODO: 2010 jan to feb
        # TODO: from jan 10th to 11th, 2010
        # TODO: jan 10th to 11th, 2010
        # TODO: jan 10 to 11, 2010
        # TODO: 10 to 11 pm

    def test_implicit_date_change(self):
        # Date change between start and end
        self.assert_range('11p',
                          datetime(2017, 6, 16, 23, 0, 0),
                          datetime(2017, 6, 17, 0, 0, 0))

        self.assert_range('11:59pm on Feb 28',
                          datetime(2018, 2, 28, 23, 59, 0),
                          datetime(2018, 3, 1, 0, 0, 0))

        self.assert_range('11:59pm on dec 31',
                          datetime(2017, 12, 31, 23, 59, 0),
                          datetime(2018, 1, 1, 0, 0, 0))

        self.assert_range('december',
                          datetime(2017, 12, 1),
                          datetime(2018, 1, 1))

        self.assert_range('between january 15th at 3 am and august 5th 5pm',
                          datetime(2018, 1, 15, 3),
                          datetime(2018, 8, 5, 17))

        self.assert_range('January to August',
                          datetime(2018, 1, 1),
                          datetime(2018, 8, 1))

        self.assert_range('Thursday to Saturday',
                          datetime(2017, 6, 22),
                          datetime(2017, 6, 24))

        self.assert_range('7pm to 8pm',
                          datetime(2017, 6, 17, 19),
                          datetime(2017, 6, 17, 20))

    def test_weekdays(self):
        day_seconds = 24 * 60 * 60
        weekdays = ('monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday')
        for i, day in enumerate(weekdays):
            start_date = 17 + (i + 2) % 7
            self.assert_range(day,
                              datetime(2017, 6, start_date),
                              datetime(2017, 6, start_date + 1))
            r = Range(day)
            self.assertEqual(len(r), day_seconds)
            self.assertEqual(r.start.weekday, i, r.start.weekday)
            self.assertEqual(r.end.weekday, (i + 1) % 7, r.end.weekday)
            self.assertEqual(r.start.isoweekday, i + 1, r.start.isoweekday)
            self.assertEqual(r.end.isoweekday, (i + 1) % 7 + 1, r.end.isoweekday)
            d = Date(day)
            self.assertTrue(d in r, '%s: %s' % (d, r))

        d = Date('now')
        r = Range('next 7 days')  # Not calendar days, unlike "next day"
        # TODO Change code to be like "next day" or create separate test
        self.assertTrue(d in r, '%s: %s' % (d, r))

    def test_offset(self):
        self.assert_range(
            'this month',
            datetime(2017, 6, 5, 4, 3, 2, 1),
            datetime(2017, 7, 5, 4, 3, 2, 1),
            offset=dict(day=5, hour=4, minute=3, second=2, microsecond=1)
        )

    def test_lengths(self):
        day = 24 * 60 * 60
        week = 7 * day
        self.assertEqual(len(Range('next 10 weeks')), 10 * week)
        self.assertEqual(len(Range('3 weeks')), 3 * week)
        self.assertEqual(len(Range('this week')), week)
        self.assertEqual(len(Range('yesterday')), day)
        self.assertEqual(len(Range('6d')), 6 * day)
        self.assertEqual(len(Range('6 d')), 6 * day)
        self.assertEqual(len(Range('6 days')), 6 * day)
        self.assertEqual(len(Range('12h')), 12 * 60 * 60)
        self.assertEqual(len(Range('6 h')), 6 * 60 * 60)
        self.assertEqual(len(Range('10m')), 60 * 10)
        self.assertEqual(len(Range('10 m')), 60 * 10)
        self.assertEqual(len(Range('10 s')), 10)
        self.assertEqual(len(Range('10s')), 10)

    def test_contains(self):
        self.assertTrue(Date('yesterday') in Range('last 7 days'))
        self.assertTrue(Date('today') in Range('this month'))
        self.assertTrue(Date('today') in Range('this month'))
        self.assertTrue(Range('this month') in Range('this year'))
        self.assertTrue(Range('this day') in Range('this week'))
        self.assertTrue(Date('yesterday') in Range('10 days'))
        self.assertTrue(Date('last tuesday') in Range('last 14 days'))
        self.assertTrue(Range('10 days') in Range('100 days'))
        self.assertTrue(Date('today') not in Range('last year'))
        # The following cases are true for some dates, including the frozen date
        self.assertTrue(Range('this week') in Range('this month'))
        self.assertTrue(Range('this week') in Range('this year'))

    def test_compare(self):
        self.assertFalse(Range('10 days') == Date('yesterday'))
        self.assertTrue(Range('next 2 weeks') > Range('1 year'))
        self.assertTrue(Range('yesterday') < Range('now'))

    def test_cut(self):
        r = Range('from january 10th 2010 to february 2nd 2010')
        r1 = r.cut(0)
        self.assertEqual(r1.start, r.start)
        self.assertEqual(r1.end, r.end)

        r1 = r.cut('10 days')
        self.assertEqual(r1.start, r.start)
        self.assertEqual(r1.end, r.end - timedelta(days=10), r1.end)

        r1 = r.cut('10 days', from_start=True)
        self.assertEqual(r1.start, r.start + timedelta(days=10))
        self.assertEqual(r1.end, r.end)

    def test_infinity(self):
        infinity = Date('infinity')
        self.assertTrue(infinity > 'now')
        self.assertTrue(infinity > 'today')
        self.assertTrue(infinity > 'next week')

        self.assertTrue(infinity not in Range('this year'))
        self.assertTrue(infinity not in Range('next 5 years'))
        self.assertTrue(Range('month') < infinity)

        r = Range('today', 'infinity')
        self.assertTrue('next 5 years' in r)
        self.assertTrue(Date('today') in r)
        self.assertTrue(infinity in r)
        self.assertFalse(infinity > r)
        self.assertFalse(r > infinity)

        r = Range('["2013-12-09 06:57:46.54502-05",infinity)')
        self.assertTrue(r.end == 'infinity')
        self.assertTrue('next 5 years' in r)
        self.assertTrue(Date('today') in r)
        self.assertTrue(infinity in r)
        self.assertFalse(infinity > r)
        self.assertFalse(r > infinity)
        self.assertEqual(r.start, datetime(2013, 12, 9, 11, 57, 46, 545020))

    def test_this(self):
        now = datetime.now()

        self.assert_range('this year',
                          datetime(2017, 1, 1),
                          datetime(2018, 1, 1))
        self.assertTrue(Date('today') in Range('this year'))

        self.assert_range('this year',
                          datetime(2017, 1, 1),
                          datetime.now(),
                          context=Context.PAST)

        self.assert_range('this year',
                          now,
                          datetime(2018, 1, 1),
                          context=Context.FUTURE)

        self.assert_range('this month',
                          datetime(2017, 6, 1),
                          datetime(2017, 7, 1))

        self.assert_range('current month',
                          datetime(2017, 6, 1),
                          datetime(2017, 7, 1))

        self.assert_range('this month',
                          datetime(2017, 6, 1),
                          now,
                          context=Context.PAST)

        self.assert_range('this month',
                          now,
                          datetime(2017, 7, 1),
                          context=Context.FUTURE)

        with freeze_time(datetime(2017, 6, 1)):
            self.assert_range('this week',
                              datetime(2017, 5, 29),
                              datetime(2017, 6, 5))

        self.assert_range('this week',
                          datetime(2017, 6, 12),
                          datetime(2017, 6, 19))

        self.assert_range('this week',
                          datetime(2017, 6, 12),
                          now,
                          context=Context.PAST)

        self.assert_range('this week',
                          now,
                          datetime(2017, 6, 19),
                          context=Context.FUTURE)

        self.assert_range('this day',
                          datetime(2017, 6, 16),
                          datetime(2017, 6, 17), )

        self.assert_range('this day',
                          datetime(2017, 6, 16),
                          now,
                          context=Context.PAST)

        self.assert_range('this day',
                          now,
                          datetime(2017, 6, 17),
                          context=Context.FUTURE)

        self.assert_range('this hour',
                          datetime(2017, 6, 16, 19),
                          datetime(2017, 6, 16, 20))

        self.assert_range('this minute',
                          datetime(2017, 6, 16, 19, 37),
                          datetime(2017, 6, 16, 19, 38))

        self.assert_range('this second',
                          datetime(2017, 6, 16, 19, 37, 22),
                          datetime(2017, 6, 16, 19, 37, 23))

        self.assert_range('this Thursday',
                          datetime(2017, 6, 22),
                          datetime(2017, 6, 23))

        self.assert_range('this Friday',
                          datetime(2017, 6, 23),
                          datetime(2017, 6, 24))

        self.assert_range('this Saturday',
                          datetime(2017, 6, 17),
                          datetime(2017, 6, 18))

    def test_last(self):
        self.assert_range('last year',
                          datetime(2016, 1, 1),
                          datetime(2017, 1, 1))

        self.assert_range('last month',
                          datetime(2017, 5, 1),
                          datetime(2017, 6, 1))

        self.assert_range('previous month',
                          datetime(2017, 5, 1),
                          datetime(2017, 6, 1))

        self.assert_range('last 5 months',
                          datetime(2017, 1, 16, 19, 37, 22),
                          datetime(2017, 6, 16, 19, 37, 22))

        self.assert_range('last 24 months',
                          datetime(2015, 6, 16, 19, 37, 22),
                          datetime(2017, 6, 16, 19, 37, 22))

        self.assert_range('last week',
                          datetime(2017, 6, 5),
                          datetime(2017, 6, 12), )

        self.assert_range('last 2 days',
                          datetime(2017, 6, 14, 19, 37, 22),
                          datetime.now())

        self.assert_range('last 5 hours',
                          datetime(2017, 6, 16, 14, 37, 22),
                          datetime(2017, 6, 16, 19, 37, 22))

        self.assert_range('last Thursday',
                          datetime(2017, 6, 15),
                          datetime(2017, 6, 16))

        self.assert_range('last Friday',
                          datetime(2017, 6, 9),
                          datetime(2017, 6, 10))

        self.assert_range('last Saturday',
                          datetime(2017, 6, 10),
                          datetime(2017, 6, 11))

    def test_next(self):
        self.assert_range('next year',
                          datetime(2018, 1, 1),
                          datetime(2019, 1, 1))

        self.assert_range('next month',
                          datetime(2017, 7, 1),
                          datetime(2017, 8, 1))

        self.assert_range('upcoming month',
                          datetime(2017, 7, 1),
                          datetime(2017, 8, 1))

        self.assert_range('next 2 months',
                          datetime(2017, 6, 16, 19, 37, 22),
                          datetime(2017, 8, 16, 19, 37, 22))

        self.assert_range('next week',
                          datetime(2017, 6, 19),
                          datetime(2017, 6, 26))

        self.assert_range('next 2 days',
                          datetime.now(),
                          datetime(2017, 6, 18, 19, 37, 22))

        self.assert_range('next 4 hours',
                          datetime(2017, 6, 16, 19, 37, 22),
                          datetime(2017, 6, 16, 23, 37, 22))

        self.assert_range('next Thursday',
                          datetime(2017, 6, 22),
                          datetime(2017, 6, 23))

        self.assert_range('next Friday',
                          datetime(2017, 6, 23),
                          datetime(2017, 6, 24))

        self.assert_range('next Saturday',
                          datetime(2017, 6, 17),
                          datetime(2017, 6, 18))

        self.assertTrue(Date('next tuesday') in Range('next 14 days'))

    def test_relative_day(self):
        self.assert_range('today',
                          datetime(2017, 6, 16),
                          datetime(2017, 6, 17))

        self.assert_range('tomorrow',
                          datetime(2017, 6, 17),
                          datetime(2017, 6, 18))

        self.assert_range('yesterday',
                          datetime(2017, 6, 15),
                          datetime(2017, 6, 16))

        self.assert_range('day after tomorrow',
                          datetime(2017, 6, 18),
                          datetime(2017, 6, 19))

        self.assert_range('day before yesterday',
                          datetime(2017, 6, 14),
                          datetime(2017, 6, 15))

    def test_ago(self):
        self.assert_range('2 years ago',
                          datetime(2015, 6, 16),
                          datetime(2015, 6, 17))

        self.assert_range('2 months ago',
                          datetime(2017, 4, 16),
                          datetime(2017, 4, 17))

        self.assert_range('2 weeks ago',
                          datetime(2017, 6, 2),
                          datetime(2017, 6, 3))

        self.assert_range('2 days ago',
                          datetime(2017, 6, 14),
                          datetime(2017, 6, 15))

        self.assert_range('2 hours ago',
                          datetime(2017, 6, 16, 17),
                          datetime(2017, 6, 16, 18))

        self.assert_range('2 minutes ago',
                          datetime(2017, 6, 16, 19, 35),
                          datetime(2017, 6, 16, 19, 36))

        self.assert_range('2 seconds ago',
                          datetime(2017, 6, 16, 19, 37, 20),
                          datetime(2017, 6, 16, 19, 37, 21))

        # Implicit change of year, month, date etc
        self.assert_range('10 months ago',
                          datetime(2016, 4, 16),
                          datetime(2016, 4, 17))

        self.assert_range('20 days ago',
                          datetime(2017, 5, 27),
                          datetime(2017, 5, 28))

        self.assert_range('20 hours ago',
                          datetime(2017, 6, 15, 23),
                          datetime(2017, 6, 16, 0))

        self.assert_range('45 minutes ago',
                          datetime(2017, 6, 16, 18, 52),
                          datetime(2017, 6, 16, 18, 53))

        self.assert_range('45 seconds ago',
                          datetime(2017, 6, 16, 19, 36, 37),
                          datetime(2017, 6, 16, 19, 36, 38))

    def test_from_now(self):
        self.assert_range('2 years from now',
                          datetime(2019, 6, 16),
                          datetime(2019, 6, 17))

        self.assert_range('2 months from now',
                          datetime(2017, 8, 16),
                          datetime(2017, 8, 17))

        self.assert_range('2 weeks from now',
                          datetime(2017, 6, 30),
                          datetime(2017, 7, 1))

        self.assert_range('2 days from now',
                          datetime(2017, 6, 18),
                          datetime(2017, 6, 19))

        self.assert_range('2 hours from now',
                          datetime(2017, 6, 16, 21),
                          datetime(2017, 6, 16, 22))

        self.assert_range('2 minutes from now',
                          datetime(2017, 6, 16, 19, 39),
                          datetime(2017, 6, 16, 19, 40))

        self.assert_range('2 seconds from now',
                          datetime(2017, 6, 16, 19, 37, 24),
                          datetime(2017, 6, 16, 19, 37, 25))

        # Implicit change of year, month, date etc
        self.assert_range('10 months from now',
                          datetime(2018, 4, 16),
                          datetime(2018, 4, 17))

        self.assert_range('20 days from now',
                          datetime(2017, 7, 6),
                          datetime(2017, 7, 7))

        self.assert_range('20 hours from now',
                          datetime(2017, 6, 17, 15),
                          datetime(2017, 6, 17, 16))

        self.assert_range('45 minutes from now',
                          datetime(2017, 6, 16, 20, 22),
                          datetime(2017, 6, 16, 20, 23))

        self.assert_range('45 seconds from now',
                          datetime(2017, 6, 16, 19, 38, 7),
                          datetime(2017, 6, 16, 19, 38, 8))

    def test_in(self):
        self.assert_range('in 2 years',
                          datetime(2019, 6, 16),
                          datetime(2019, 6, 17))

        self.assert_range('in 2 months',
                          datetime(2017, 8, 16),
                          datetime(2017, 8, 17))

        self.assert_range('in 2 weeks',
                          datetime(2017, 6, 30),
                          datetime(2017, 7, 1))

        self.assert_range('in 2 days',
                          datetime(2017, 6, 18),
                          datetime(2017, 6, 19))

        self.assert_range('in 2 hours',
                          datetime(2017, 6, 16, 21),
                          datetime(2017, 6, 16, 22))

        self.assert_range('in 2 minutes',
                          datetime(2017, 6, 16, 19, 39),
                          datetime(2017, 6, 16, 19, 40))

        self.assert_range('in 2 seconds',
                          datetime(2017, 6, 16, 19, 37, 24),
                          datetime(2017, 6, 16, 19, 37, 25))

        # Implicit change of year, month, date etc
        self.assert_range('in 10 months',
                          datetime(2018, 4, 16),
                          datetime(2018, 4, 17))

        self.assert_range('in 20 days',
                          datetime(2017, 7, 6),
                          datetime(2017, 7, 7))

        self.assert_range('in 20 hours',
                          datetime(2017, 6, 17, 15),
                          datetime(2017, 6, 17, 16))

        self.assert_range('in 45 minutes',
                          datetime(2017, 6, 16, 20, 22),
                          datetime(2017, 6, 16, 20, 23))

        self.assert_range('in 45 seconds',
                          datetime(2017, 6, 16, 19, 38, 7),
                          datetime(2017, 6, 16, 19, 38, 8))

    def test_since(self):
        now = datetime.now()
        self.assert_range('since last may', datetime(2017, 5, 1), now)
        self.assert_range('since last Friday', datetime(2017, 6, 9), now)
        self.assert_range('since last Saturday', datetime(2017, 6, 10), now)
        self.assert_range('since last Thursday', datetime(2017, 6, 15), now)
        self.assert_range('since last year', datetime(2016, 1, 1), now)
        self.assert_range('since last month', datetime(2017, 5, 1), now)
        self.assert_range('since last week', datetime(2017, 6, 5), now)
        self.assert_range('since yesterday', datetime(2017, 6, 15), now)

        self.assert_range('since 2016', datetime(2016, 1, 1), now)
        self.assert_range('since July', datetime(2016, 7, 1), now)
        self.assert_range('since April 2016', datetime(2016, 4, 1), now)
        self.assert_range('since April 11, 2016', datetime(2016, 4, 11), now)
        self.assert_range('since Friday', datetime(2017, 6, 9), now)
        self.assert_range('since Saturday', datetime(2017, 6, 10), now)
        self.assert_range('since Thursday', datetime(2017, 6, 15), now)

        self.assert_range('since this month', datetime(2017, 6, 1), now)
        self.assert_range('since this week', datetime(2017, 6, 12), now)
        self.assert_range('since today', datetime(2017, 6, 16), now)
        self.assert_range('since this morning', datetime(2017, 6, 16, 9), now)
        self.assert_range('since 4pm', datetime(2017, 6, 16, 16), now)

        self.assert_range('since 2 years ago', datetime(2015, 6, 16), now)
        self.assert_range('since 2 months ago', datetime(2017, 4, 16), now)
        self.assert_range('since 2 weeks ago', datetime(2017, 6, 2), now)
        self.assert_range('since 2 days ago', datetime(2017, 6, 14), now)
        self.assert_range('since 2 hours ago', datetime(2017, 6, 16, 17), now)
        self.assert_range('since 2 minutes ago', datetime(2017, 6, 16, 19, 35), now)
        self.assert_range('since 2 seconds ago', datetime(2017, 6, 16, 19, 37, 20), now)

        # Implicit change of year, month, date etc
        self.assert_range('since 10 months ago', datetime(2016, 4, 16), now)
        self.assert_range('since 20 days ago', datetime(2017, 5, 27), now)
        self.assert_range('since 20 hours ago', datetime(2017, 6, 15, 23), now)
        self.assert_range('since 45 minutes ago', datetime(2017, 6, 16, 18, 52), now)
        self.assert_range('since 45 seconds ago', datetime(2017, 6, 16, 19, 36, 37), now)

        # TODO 'Since tomorrow' etc: error or guess or infinity or unknown

    def test_until(self):
        now = datetime.now()
        self.assert_range('until next may', now, datetime(2018, 5, 1))
        self.assert_range('until next Friday', now, datetime(2017, 6, 23))
        self.assert_range('until next Saturday', now, datetime(2017, 6, 17))
        self.assert_range('until next Thursday', now, datetime(2017, 6, 22))
        self.assert_range('until next year', now, datetime(2018, 1, 1))
        self.assert_range('until next month', now, datetime(2017, 7, 1))
        self.assert_range('until next week', now, datetime(2017, 6, 19))
        self.assert_range('until tomorrow', now, datetime(2017, 6, 17))

        self.assert_range('until 2018', now, datetime(2018, 1, 1))
        self.assert_range('until April', now, datetime(2018, 4, 1))
        self.assert_range('until April 2018', now, datetime(2018, 4, 1))
        self.assert_range('until April 11, 2018', now, datetime(2018, 4, 11))
        self.assert_range('until Friday', now, datetime(2017, 6, 23))
        self.assert_range('until Saturday', now, datetime(2017, 6, 17))
        self.assert_range('until Thursday', now, datetime(2017, 6, 22))

        self.assert_range('until 2 years from now', now, datetime(2019, 6, 16))
        self.assert_range('until 2 months from now', now, datetime(2017, 8, 16))
        self.assert_range('until 2 weeks from now', now, datetime(2017, 6, 30))
        self.assert_range('until 2 days from now', now, datetime(2017, 6, 18))
        self.assert_range('until 2 hours from now', now, datetime(2017, 6, 16, 21))
        self.assert_range('until 2 minutes from now', now, datetime(2017, 6, 16, 19, 39))
        self.assert_range('until 2 seconds from now', now, datetime(2017, 6, 16, 19, 37, 24))

        # Implicit change of year, month, date etc
        self.assert_range('until 10 months from now', now, datetime(2018, 4, 16))
        self.assert_range('until 20 days from now', now, datetime(2017, 7, 6))
        self.assert_range('until 20 hours from now', now, datetime(2017, 6, 17, 15))
        self.assert_range('until 45 minutes from now', now, datetime(2017, 6, 16, 20, 22))
        self.assert_range('until 45 seconds from now', now, datetime(2017, 6, 16, 19, 38, 7))

        # TODO "Until yesterday" etc: error or guess or infinity or unknown
        # TODO "Until the start of today" vs "Until the end of today"

    def test_by(self):
        now = datetime.now()

        self.assert_range('by next may', now, datetime(2018, 5, 1))
        self.assert_range('by next Friday', now, datetime(2017, 6, 23))
        self.assert_range('by next Saturday', now, datetime(2017, 6, 17))
        self.assert_range('by next Thursday', now, datetime(2017, 6, 22))
        self.assert_range('by next year', now, datetime(2018, 1, 1))
        self.assert_range('by next month', now, datetime(2017, 7, 1))
        self.assert_range('by next week', now, datetime(2017, 6, 19))
        self.assert_range('by tomorrow', now, datetime(2017, 6, 17))

        self.assert_range('by 2018', now, datetime(2018, 1, 1))
        self.assert_range('by April', now, datetime(2018, 4, 1))
        self.assert_range('by April 2018', now, datetime(2018, 4, 1))
        self.assert_range('by April 11, 2018', now, datetime(2018, 4, 11))
        self.assert_range('by Friday', now, datetime(2017, 6, 23))
        self.assert_range('by Saturday', now, datetime(2017, 6, 17))
        self.assert_range('by Thursday', now, datetime(2017, 6, 22))

        self.assert_range('by 2 years from now', now, datetime(2019, 6, 16))
        self.assert_range('by 2 months from now', now, datetime(2017, 8, 16))
        self.assert_range('by 2 weeks from now', now, datetime(2017, 6, 30))
        self.assert_range('by 2 days from now', now, datetime(2017, 6, 18))
        self.assert_range('by 2 hours from now', now, datetime(2017, 6, 16, 21))
        self.assert_range('by 2 minutes from now', now, datetime(2017, 6, 16, 19, 39))
        self.assert_range('by 2 seconds from now', now, datetime(2017, 6, 16, 19, 37, 24))

        # Implicit change of year, month, date etc
        self.assert_range('by 10 months from now', now, datetime(2018, 4, 16))
        self.assert_range('by 20 days from now', now, datetime(2017, 7, 6))
        self.assert_range('by 20 hours from now', now, datetime(2017, 6, 17, 15))
        self.assert_range('by 45 minutes from now', now, datetime(2017, 6, 16, 20, 22))
        self.assert_range('by 45 seconds from now', now, datetime(2017, 6, 16, 19, 38, 7))

        # TODO "by yesterday" etc: error or guess or infinity or unknown
        # TODO "by the start of today" vs "by the end of today"

    def test_week_start(self):
        self.assert_range('this week',
                          datetime(2017, 6, 11),
                          datetime(2017, 6, 18),
                          week_start=0)

        self.assert_range('this week',
                          datetime(2017, 6, 11),
                          datetime(2017, 6, 18),
                          week_start=7)

        self.assert_range('this week',
                          datetime(2017, 6, 11),
                          datetime.now(),
                          context=Context.PAST,
                          week_start=0)

        self.assert_range('this week',
                          datetime.now(),
                          datetime(2017, 6, 18),
                          context=Context.FUTURE,
                          week_start=0)

        self.assert_range('last week',
                          datetime(2017, 6, 4),
                          datetime(2017, 6, 11),
                          week_start=0)

        self.assert_range('next week',
                          datetime(2017, 6, 18),
                          datetime(2017, 6, 25),
                          week_start=0)

        now = datetime.now()

        self.assert_range('since last week',
                          datetime(2017, 6, 4),
                          now,
                          week_start=0)

        self.assert_range('since this week',
                          datetime(2017, 6, 11),
                          now,
                          week_start=0)

        self.assert_range('until next week',
                          now,
                          datetime(2017, 6, 18),
                          week_start=0)

        # Other time references are unchanged
        self.assert_range('this month',
                          datetime(2017, 6, 1, 0, 0, 0),
                          datetime(2017, 7, 1, 0, 0, 0),
                          week_start=0)

        self.assert_range('monday',
                          datetime(2017, 6, 19),
                          datetime(2017, 6, 20),
                          week_start=0)

    def test_until_implicit(self):
        now = datetime.now()

        # 1 year (till now)
        start, end = Range('1 year')
        self.assertEqual(start.year, now.year - 1)
        self.assertEqual(start.month, now.month)
        self.assertEqual(start.day, now.day)
        self.assertEqual(start.hour, now.hour)
        self.assertEqual(start.minute, now.minute)
        self.assertEqual(end.year, now.year)
        self.assertEqual(end.month, now.month)
        self.assertEqual(end.day, now.day)
        self.assertEqual(end.hour, now.hour)
        self.assertEqual(end.minute, now.minute)

    def test_context_past(self):
        now = datetime.now()
        # Current period
        self.assert_range('2017',
                          datetime(2017, 1, 1),
                          now,
                          context=Context.PAST)

        self.assert_range('june',
                          datetime(2017, 6, 1),
                          now,
                          context=Context.PAST)

        self.assert_range('2017 june',
                          datetime(2017, 6, 1),
                          now,
                          context=Context.PAST)

        self.assert_range('today',
                          datetime(2017, 6, 16),
                          now,
                          context=Context.PAST)

        self.assert_range('friday',
                          datetime(2017, 6, 16),
                          now,
                          context=Context.PAST)

        # Specified past - no effect
        self.assert_range('2000',
                          datetime(2000, 1, 1),
                          datetime(2001, 1, 1),
                          context=Context.PAST)

        self.assert_range('last may',
                          datetime(2017, 5, 1),
                          datetime(2017, 6, 1),
                          context=Context.PAST)

        self.assert_range('2017 may',
                          datetime(2017, 5, 1),
                          datetime(2017, 6, 1),
                          context=Context.PAST)

        self.assert_range('last thursday',
                          datetime(2017, 6, 15),
                          datetime(2017, 6, 16),
                          context=Context.PAST)

        # Specified future - no effect
        self.assert_range('2018',
                          datetime(2018, 1, 1),
                          datetime(2019, 1, 1),
                          context=Context.PAST)

        self.assert_range('july',
                          datetime(2017, 7, 1),
                          datetime(2017, 8, 1),
                          context=Context.PAST)

        self.assert_range('2017 july',
                          datetime(2017, 7, 1),
                          datetime(2017, 8, 1),
                          context=Context.PAST)

        self.assert_range('saturday',
                          datetime(2017, 6, 17),
                          datetime(2017, 6, 18),
                          context=Context.PAST)

    def test_context_future(self):
        now = datetime.now()
        # Current period
        self.assert_range('2017',
                          now,
                          datetime(2018, 1, 1),
                          context=Context.FUTURE)

        self.assert_range('june',
                          now,
                          datetime(2017, 7, 1),
                          context=Context.FUTURE)

        self.assert_range('2017 june',
                          now,
                          datetime(2017, 7, 1),
                          context=Context.FUTURE)

        self.assert_range('today',
                          now,
                          datetime(2017, 6, 17),
                          context=Context.FUTURE)

        self.assert_range('friday',
                          now,
                          datetime(2017, 6, 17),
                          context=Context.FUTURE)

        # Specified past - no effect
        self.assert_range('2000',
                          datetime(2000, 1, 1),
                          datetime(2001, 1, 1),
                          context=Context.FUTURE)

        self.assert_range('last may',
                          datetime(2017, 5, 1),
                          datetime(2017, 6, 1),
                          context=Context.FUTURE)

        self.assert_range('2017 may',
                          datetime(2017, 5, 1),
                          datetime(2017, 6, 1),
                          context=Context.FUTURE)

        self.assert_range('thursday',
                          datetime(2017, 6, 22),
                          datetime(2017, 6, 23),
                          context=Context.FUTURE)

        # Specified future - no effect
        self.assert_range('2018',
                          datetime(2018, 1, 1),
                          datetime(2019, 1, 1),
                          context=Context.FUTURE)

        self.assert_range('july',
                          datetime(2017, 7, 1),
                          datetime(2017, 8, 1),
                          context=Context.FUTURE)

        self.assert_range('2017 july',
                          datetime(2017, 7, 1),
                          datetime(2017, 8, 1),
                          context=Context.FUTURE)

        self.assert_range('saturday',
                          datetime(2017, 6, 17),
                          datetime(2017, 6, 18),
                          context=Context.FUTURE)

    def context_prev(self):
        self.assert_range('2017',               # No effect
                          datetime(2017, 1, 1),
                          datetime(2018, 1, 1),
                          context=Context.PREV)

        self.assert_range('june',
                          datetime(2016, 6, 1),
                          datetime(2016, 7, 1),
                          context=Context.PREV)

        self.assert_range('2017 june',          # No effect
                          datetime(2017, 6, 1),
                          datetime(2017, 7, 1),
                          context=Context.PREV)

        self.assert_range('2018',
                          datetime(2018, 1, 1),
                          datetime(2019, 1, 1),
                          context=Context.PREV)

        self.assert_range('april',
                          datetime(2017, 4, 1),
                          datetime(2017, 5, 1),
                          context=Context.PREV)

        self.assert_range('july',
                          datetime(2016, 7, 1),
                          datetime(2016, 8, 1),
                          context=Context.PREV)

        self.assert_range('2017 july',
                          datetime(2017, 7, 1),
                          datetime(2017, 8, 1),
                          context=Context.PREV)

    def context_next(self):
        self.assert_range('2017',               # No effect
                          datetime(2017, 1, 1),
                          datetime(2018, 1, 1),
                          context=Context.NEXT)

        self.assert_range('june',
                          datetime(2018, 6, 1),
                          datetime(2018, 7, 1),
                          context=Context.NEXT)

        self.assert_range('2017 june',          # No effect
                          datetime(2017, 6, 1),
                          datetime(2017, 7, 1),
                          context=Context.NEXT)


        self.assert_range('2018',
                          datetime(2018, 1, 1),
                          datetime(2019, 1, 1),
                          context=Context.NEXT)

        self.assert_range('april',
                          datetime(2018, 4, 1),
                          datetime(2018, 5, 1),
                          context=Context.NEXT)

        self.assert_range('july',
                          datetime(2017, 7, 1),
                          datetime(2017, 8, 1),
                          context=Context.NEXT)

        self.assert_range('2017 july',
                          datetime(2017, 7, 1),
                          datetime(2017, 8, 1),
                          context=Context.NEXT)

    def test_fractional_duration(self):
        now = datetime.now()
        _3days = timedelta(days=3)
        
        self.assert_range('last 2.5 years',
                          datetime(2014, 12, 16), now,
                          start_tolerance=_3days)

        self.assert_range('last 2.5 months',
                          datetime(2017, 3, 30), now,
                          start_tolerance=_3days)

        self.assert_range('last 2.5 days',
                          datetime(2017, 6, 14, 7, 37, 22), now)

        self.assert_range('last 2.5 hours',
                          datetime(2017, 6, 16, 17, 7, 22), now)

        self.assert_range('next 2.5 years',
                          now, datetime(2019, 12, 16),
                          end_tolerance=_3days)

        self.assert_range('next 2.5 months',
                          now, datetime(2017, 8, 30),
                          end_tolerance=_3days)

        self.assert_range('next 2.5 days',
                          now, datetime(2017, 6, 19, 7, 37, 22))

        self.assert_range('next 2.5 hours',
                          now, datetime(2017, 6, 16, 22, 7, 22))

        self.assert_range('2.5 years ago',
                          datetime(2014, 12, 16),
                          datetime(2014, 12, 17),
                          start_tolerance=_3days,
                          end_tolerance=_3days)

        self.assert_range('2.5 months ago',
                          datetime(2017, 4, 1),
                          datetime(2017, 4, 2),
                          start_tolerance=_3days,
                          end_tolerance=_3days)

        self.assert_range('2.5 weeks ago',
                          datetime(2017, 5, 30, 7, 37, 22),
                          datetime(2017, 5, 31, 7, 37, 22))

        self.assert_range('2.5 days ago',
                          datetime(2017, 6, 14, 7, 37, 22),
                          datetime(2017, 6, 15, 7, 37, 22))

        self.assert_range('2.5 hours ago',
                          datetime(2017, 6, 16, 17, 7, 22),
                          datetime(2017, 6, 16, 18, 7, 22))

        self.assert_range('2.5 minutes ago',
                          datetime(2017, 6, 16, 19, 34, 52),
                          datetime(2017, 6, 16, 19, 35, 52))

        self.assert_range('2.5 seconds ago',
                          datetime(2017, 6, 16, 19, 37, 19, 500000),
                          datetime(2017, 6, 16, 19, 37, 20, 500000))

        self.assert_range('in 2.5 years',
                          datetime(2019, 12, 16),
                          datetime(2019, 12, 17),
                          start_tolerance=_3days,
                          end_tolerance=_3days)

        self.assert_range('in 2.5 months',
                          datetime(2017, 9, 1),
                          datetime(2017, 9, 2),
                          start_tolerance=_3days,
                          end_tolerance=_3days)

        self.assert_range('in 2.5 weeks',
                          datetime(2017, 7, 4, 7, 37, 22),
                          datetime(2017, 7, 5, 7, 37, 22))

        self.assert_range('in 2.5 days',
                          datetime(2017, 6, 19, 7, 37, 22),
                          datetime(2017, 6, 20, 7, 37, 22))

        self.assert_range('in 2.5 hours',
                          datetime(2017, 6, 16, 22, 7, 22),
                          datetime(2017, 6, 16, 23, 7, 22))

        self.assert_range('in 2.5 minutes',
                          datetime(2017, 6, 16, 19, 39, 52),
                          datetime(2017, 6, 16, 19, 40, 52))

        self.assert_range('in 2.5 seconds',
                          datetime(2017, 6, 16, 19, 37, 24, 500000),
                          datetime(2017, 6, 16, 19, 37, 25, 500000))

        self.assert_range('since 2.5 years ago',
                          datetime(2014, 12, 16),
                          now,
                          start_tolerance=_3days)

        self.assert_range('since 2.5 months ago',
                          datetime(2017, 4, 1),
                          now,
                          start_tolerance=_3days)

        self.assert_range('since 2.5 weeks ago',
                          datetime(2017, 5, 30, 7, 37, 22),
                          now)

        self.assert_range('since 2.5 days ago',
                          datetime(2017, 6, 14, 7, 37, 22),
                          now)

        self.assert_range('since 2.5 hours ago',
                          datetime(2017, 6, 16, 17, 7, 22),
                          now)

        self.assert_range('since 2.5 minutes ago',
                          datetime(2017, 6, 16, 19, 34, 52),
                          now)

        self.assert_range('since 2.5 seconds ago',
                          datetime(2017, 6, 16, 19, 37, 19, 500000),
                          now)

    def test_weekend(self):
        now = datetime.now()

        # Frozen date is on a weekend
        self.assert_range('this weekend',
                          datetime(2017, 6, 16, WEEKEND_START_HOUR),
                          datetime(2017, 6, 19, WEEKEND_END_HOUR))

        self.assert_range('this weekend',
                          datetime(2017, 6, 16, WEEKEND_START_HOUR),
                          now,
                          context=Context.PAST)

        self.assert_range('this weekend',
                          now,
                          datetime(2017, 6, 19, WEEKEND_END_HOUR),
                          context=Context.FUTURE)

        self.assert_range('last weekend',
                          datetime(2017, 6, 9, WEEKEND_START_HOUR),
                          datetime(2017, 6, 12, WEEKEND_END_HOUR))

        self.assert_range('next weekend',
                          datetime(2017, 6, 23, WEEKEND_START_HOUR),
                          datetime(2017, 6, 26, WEEKEND_END_HOUR))

        self.assert_range('since this weekend',
                          datetime(2017, 6, 16, WEEKEND_START_HOUR),
                          now)

        self.assert_range('since last weekend',
                          datetime(2017, 6, 9, WEEKEND_START_HOUR),
                          now)

        self.assert_range('until next weekend',
                          now,
                          datetime(2017, 6, 23, WEEKEND_START_HOUR))

        # On a non-weekend
        with freeze_time('2017-06-14 10:43:09'):
            self.assert_range('this weekend',
                              datetime(2017, 6, 16, WEEKEND_START_HOUR),
                              datetime(2017, 6, 19, WEEKEND_END_HOUR))

            self.assert_range('this weekend',
                              datetime(2017, 6, 16, WEEKEND_START_HOUR),
                              datetime(2017, 6, 19, WEEKEND_END_HOUR),
                              context=Context.PAST)

            self.assert_range('this weekend',
                              datetime(2017, 6, 16, WEEKEND_START_HOUR),
                              datetime(2017, 6, 19, WEEKEND_END_HOUR),
                              context=Context.FUTURE)

            self.assert_range('last weekend',
                              datetime(2017, 6, 9, WEEKEND_START_HOUR),
                              datetime(2017, 6, 12, WEEKEND_END_HOUR))

            self.assert_range('next weekend',
                              datetime(2017, 6, 16, WEEKEND_START_HOUR),
                              datetime(2017, 6, 19, WEEKEND_END_HOUR))

            self.assert_range('since last weekend',
                              datetime(2017, 6, 9, WEEKEND_START_HOUR),
                              datetime.now())

            self.assert_range('until next weekend',
                              datetime.now(),
                              datetime(2017, 6, 16, WEEKEND_START_HOUR))

        # Not affected by week start day and time
        self.assert_range('this weekend',
                          datetime(2017, 6, 16, WEEKEND_START_HOUR),
                          datetime(2017, 6, 19, WEEKEND_END_HOUR),
                          week_start=0)

        with freeze_time('2017-06-14 10:43:09'):
            self.assert_range('this weekend',
                              datetime(2017, 6, 16, WEEKEND_START_HOUR),
                              datetime(2017, 6, 19, WEEKEND_END_HOUR),
                              week_start=0)


def main():
    os.environ['TZ'] = 'UTC'
    time.tzset()
    unittest.main()


if __name__ == '__main__':
    main()
