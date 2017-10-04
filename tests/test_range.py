from datetime import datetime, date, timedelta
import os
import time
import unittest

from freezegun import freeze_time

from timestring.Range import Date, Range, CONTEXT_PAST, CONTEXT_FUTURE
from timestring.Date import WEEKDAY_ORDINALS_DE, RELATIVE_DAYS_DE


@freeze_time('2017-06-16 19:37:22')
class RangeTest(unittest.TestCase):
    def assert_range(self, range_str, expected_start: datetime,
                     expected_end: datetime, context=None):
        _range = Range(range_str, context=context)

        self.assertEqual(_range.start,
                         expected_start,
                        '\n          Text: ' + range_str
                         + '\nExpected start: ' + str(expected_start)
                         + '\n  Actual start: ' + str(_range.start))
        self.assertEqual(_range.end,
                         expected_end,
                         '\n        Text: ' + range_str
                         + '\nExpected end: ' + str(expected_end)
                         + '\n  Actual end: ' + str(_range.end))

    def test_date_formats(self):
        """This should be in test_date.py, except that date ranges start at
        midnight, while Date() produces a date with the current time."""
        for date_str in [
            'September 5, 2012',
            '2012 5 September',
            'sep 5 2012',
            'sept 5 2012',
            "sep 5th, '12",
            '5th September, 2012',
            #TODO: 5th of September, 2012
            '2012/9/5',
            '2012-09-5T',
            '9/5/2012',
        ]:
            self.assert_range(date_str,
                              datetime(2012, 9, 5),
                              datetime(2012, 9, 6))

        # TODO: 13/5/2012

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


    def test_context(self):
        # Current period
        self.assert_range('2017',
                          datetime(2017, 1, 1),
                          datetime.now(),
                          context=CONTEXT_PAST)

        self.assert_range('2017',
                          datetime.now(),
                          datetime(2018, 1, 1),
                          context=CONTEXT_FUTURE)

        self.assert_range('june',
                          datetime(2017, 6, 1),
                          datetime.now(),
                          context=CONTEXT_PAST)

        self.assert_range('june',
                          datetime.now(),
                          datetime(2017, 7, 1),
                          context=CONTEXT_FUTURE)

        self.assert_range('2017 june',
                          datetime(2017, 6, 1),
                          datetime.now(),
                          context=CONTEXT_PAST)

        self.assert_range('2017 june',
                          datetime.now(),
                          datetime(2017, 7, 1),
                          context=CONTEXT_FUTURE)

        # A past period - no effect
        self.assert_range('2000',
                          datetime(2000, 1, 1),
                          datetime(2001, 1, 1),
                          context=CONTEXT_PAST)

        self.assert_range('2000',
                          datetime(2000, 1, 1),
                          datetime(2001, 1, 1),
                          context=CONTEXT_FUTURE)

        self.assert_range('last may',
                          datetime(2017, 5, 1),
                          datetime(2017, 6, 1),
                          context=CONTEXT_PAST)

        self.assert_range('last may',
                          datetime(2017, 5, 1),
                          datetime(2017, 6, 1),
                          context=CONTEXT_FUTURE)

        self.assert_range('2017 may',
                          datetime(2017, 5, 1),
                          datetime(2017, 6, 1),
                          context=CONTEXT_PAST)

        self.assert_range('2017 may',
                          datetime(2017, 5, 1),
                          datetime(2017, 6, 1),
                          context=CONTEXT_FUTURE)

        # A future period - no effect
        self.assert_range('2018',
                          datetime(2018, 1, 1),
                          datetime(2019, 1, 1),
                          context=CONTEXT_PAST)

        self.assert_range('2018',
                          datetime(2018, 1, 1),
                          datetime(2019, 1, 1),
                          context=CONTEXT_FUTURE)

        self.assert_range('july',
                          datetime(2017, 7, 1),
                          datetime(2017, 8, 1),
                          context=CONTEXT_PAST)

        self.assert_range('july',
                          datetime(2017, 7, 1),
                          datetime(2017, 8, 1),
                          context=CONTEXT_FUTURE)

        self.assert_range('2017 july',
                          datetime(2017, 7, 1),
                          datetime(2017, 8, 1),
                          context=CONTEXT_PAST)

        self.assert_range('2017 july',
                          datetime(2017, 7, 1),
                          datetime(2017, 8, 1),
                          context=CONTEXT_FUTURE)

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

    def test_explicit_end(self):
        _range = Range('2012 feb 2 1:13PM to 6:41 am on sept 8 2012')
        self.assertEqual(_range[0].year, 2012)
        self.assertEqual(_range[0].month, 2)
        self.assertEqual(_range[0].day, 2)
        self.assertEqual(_range[0].hour, 13)
        self.assertEqual(_range[0].minute, 13)
        self.assertEqual(_range[1].year, 2012)
        self.assertEqual(_range[1].month, 9)
        self.assertEqual(_range[1].day, 8)
        self.assertEqual(_range[1].hour, 6)
        self.assertEqual(_range[1].minute, 41)

        self.assert_range('from jan 10 2010 5 am to jan 10, 2010 9 am',
                          datetime(2010, 1, 10, 5),
                          datetime(2010, 1, 10, 9))

        self.assert_range('from january 10th 2010 to jan 12th 2010',
                          datetime(2010, 1, 10),
                          datetime(2010, 1, 12))

        self.assert_range('january 10 to jan 12',
                          datetime(2018, 1, 10),
                          datetime(2018, 1, 12))

        self.assert_range('between january 10 and jan 12',
                          datetime(2018, 1, 10),
                          datetime(2018, 1, 12))

        self.assert_range('10am to 11pm',
                          datetime(2017, 6, 16, 10),
                          datetime(2017, 6, 16, 23))

        self.assert_range('10pm to 11am',
                          datetime(2017, 6, 16, 22),
                          datetime(2017, 6, 17, 11))

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

    def test_implicit_end_year_is_next_year(self):
        _range = Range("between january 15th at 3 am and august 5th 5pm")
        self.assertEqual(_range[0].year, 2018)
        self.assertEqual(_range[0].month, 1)
        self.assertEqual(_range[0].day, 15)
        self.assertEqual(_range[0].hour, 3)
        self.assertEqual(_range[0].minute, 0)
        self.assertEqual(_range[0].second, 0)
        self.assertEqual(_range[1].year, 2018)
        self.assertEqual(_range[1].month, 8)
        self.assertEqual(_range[1].day, 5)
        self.assertEqual(_range[1].hour, 17)
        self.assertEqual(_range[1].minute, 0)
        self.assertEqual(_range[1].second, 0)

    def test_relative_year(self):
        self.assert_range('this year',
                          datetime(2017, 1, 1, 0, 0, 0),
                          datetime(2018, 1, 1, 0, 0, 0))

        self.assert_range('this year',
                          datetime(2017, 1, 1, 0, 0, 0),
                          datetime.now(),
                          context=CONTEXT_PAST)

        self.assert_range('this year',
                          datetime.now(),
                          datetime(2018, 1, 1, 0, 0, 0),
                          context=CONTEXT_FUTURE)

        self.assert_range('last year',
                          datetime(2016, 1, 1, 0, 0, 0),
                          datetime(2017, 1, 1, 0, 0, 0))

        self.assert_range('next year',
                          datetime(2018, 1, 1, 0, 0, 0),
                          datetime(2019, 1, 1, 0, 0, 0))

    def test_relative_month(self):
        self.assert_range('this month',
                          datetime(2017, 6, 1, 0, 0, 0),
                          datetime(2017, 7, 1, 0, 0, 0))

        self.assert_range('current month',
                          datetime(2017, 6, 1, 0, 0, 0),
                          datetime(2017, 7, 1, 0, 0, 0))

        self.assert_range('this month',
                          datetime(2017, 6, 1, 0, 0, 0),
                          datetime.now(),
                          context=CONTEXT_PAST)

        self.assert_range('this month',
                          datetime.now(),
                          datetime(2017, 7, 1, 0, 0, 0),
                          context=CONTEXT_FUTURE)

        self.assert_range('next month',
                          datetime(2017, 7, 1, 0, 0, 0),
                          datetime(2017, 8, 1, 0, 0, 0))

        self.assert_range('upcoming month',
                          datetime(2017, 7, 1, 0, 0, 0),
                          datetime(2017, 8, 1, 0, 0, 0))

        self.assert_range('last month',
                          datetime(2017, 5, 1, 0, 0, 0),
                          datetime(2017, 6, 1, 0, 0, 0))

        self.assert_range('previous month',
                          datetime(2017, 5, 1, 0, 0, 0),
                          datetime(2017, 6, 1, 0, 0, 0))

        self.assert_range('next 2 months',
                          datetime(2017, 6, 16, 19, 37, 22),
                          datetime(2017, 8, 16, 19, 37, 22))

        self.assert_range('last 5 months',
                          datetime(2017, 1, 16, 19, 37, 22),
                          datetime(2017, 6, 16, 19, 37, 22))

        self.assert_range('last 24 months',
                          datetime(2015, 6, 16, 19, 37, 22),
                          datetime(2017, 6, 16, 19, 37, 22))

    def test_relative_week(self):
        self.assert_range('this week',
                          datetime(2017, 6, 12),
                          datetime(2017, 6, 19))

        self.assert_range('this week',
                          datetime(2017, 6, 12),
                          datetime.now(),
                          context=CONTEXT_PAST)

        self.assert_range('this week',
                          datetime.now(),
                          datetime(2017, 6, 19),
                          context=CONTEXT_FUTURE)

        self.assert_range('last week',
                          datetime(2017, 6, 5),
                          datetime(2017, 6, 12),)

        self.assert_range('next week',
                          datetime(2017, 6, 19),
                          datetime(2017, 6, 26))

    def test_relative_day(self):
        self.assert_range('today',
                          datetime(2017, 6, 16),
                          datetime(2017, 6, 17),)

        self.assert_range('today',
                          datetime(2017, 6, 16),
                          datetime.now(),
                          context=CONTEXT_PAST)

        self.assert_range('today',
                          datetime.now(),
                          datetime(2017, 6, 17),
                          context=CONTEXT_FUTURE)

        self.assert_range('tomorrow',
                          datetime(2017, 6, 17),
                          datetime(2017, 6, 18))

        self.assert_range('day after tomorrow',
                          datetime(2017, 6, 18),
                          datetime(2017, 6, 19))

        self.assert_range('yesterday',
                          datetime(2017, 6, 15),
                          datetime(2017, 6, 16))

        self.assert_range('day before yesterday',
                          datetime(2017, 6, 14),
                          datetime(2017, 6, 15))

        self.assert_range('next 2 days',
                          datetime.now(),
                          datetime.now() + timedelta(days=2))

        self.assert_range('last 2 days',
                          datetime.now() - timedelta(days=2),
                          datetime.now())

    def test_relative_weekday_today(self):
        """
        For current day of week. E.g., if today is Friday:
            'Friday' = 'this Friday' = Friday this week
            'next Friday' = Friday of next week
            'last Friday' = Friday of last week
        """
        weekday = datetime.now().strftime('%A')

        self.assert_range(weekday,
                          datetime(2017, 6, 23),
                          datetime(2017, 6, 24))

        self.assert_range('this ' + weekday,
                          datetime(2017, 6, 23),
                          datetime(2017, 6, 24))

        self.assert_range(weekday,
                          datetime(2017, 6, 23),
                          datetime(2017, 6, 24))

        self.assert_range(weekday,
                          datetime(2017, 6, 23),
                          datetime(2017, 6, 24))

        self.assert_range('next ' + weekday,
                          datetime(2017, 6, 23),
                          datetime(2017, 6, 24))

        self.assert_range('upcoming ' + weekday,
                          datetime(2017, 6, 23),
                          datetime(2017, 6, 24))

        self.assert_range('last ' + weekday,
                          datetime(2017, 6, 9),
                          datetime(2017, 6, 10))

        self.assert_range('previous ' + weekday,
                          datetime(2017, 6, 9),
                          datetime(2017, 6, 10))

    def test_relative_weekday_yesterday(self):
        """
        For past days of week
        If today is Friday, 'Thursday' = 'this Thursday' = 'next Thursday'
        """
        yesterday = datetime.now() + timedelta(days=-1)
        weekday = yesterday.strftime('%A')

        start = datetime(2017, 6, 22)
        end = datetime(2017, 6, 23)

        self.assert_range(weekday, start, end)
        self.assert_range('this ' + weekday, start, end)
        self.assert_range('next ' + weekday, start, end)
        self.assert_range('last ' + weekday,
                          datetime(2017, 6, 15),
                          datetime(2017, 6, 16))

    def test_relative_weekday_tomorrow(self):
        """
        For future days of week
        If today is Friday, 'Saturday' = 'this Saturday' = 'next Saturday'
        """
        tomorrow = datetime.now() + timedelta(days=1)
        weekday = tomorrow.strftime('%A')

        start = datetime(2017, 6, 17)
        end = datetime(2017, 6, 18)

        self.assert_range(weekday, start, end)
        self.assert_range('this ' + weekday, start, end)
        self.assert_range('next ' + weekday, start, end)
        self.assert_range('last ' + weekday,
                          datetime(2017, 6, 10),
                          datetime(2017, 6, 11))

    def test_relative_hour(self):
        self.assert_range('last 5 hours',
                          datetime(2017, 6, 16, 14, 37, 22),
                          datetime(2017, 6, 16, 19, 37, 22))

        self.assert_range('next 4 hours',
                          datetime(2017, 6, 16, 19, 37, 22),
                          datetime(2017, 6, 16, 23, 37, 22))

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

        # TODO Error cases such as "Since tomorrow"

    def test_weekdays_de(self):
        day_seconds = 24 * 60 * 60

        def test_weekday(day_name, iso):
            start_date = 17 + (iso + 1) % 7
            self.assert_range(day_name,
                              datetime(2017, 6, start_date),
                              datetime(2017, 6, start_date + 1))
            r = Range(day_name)
            self.assertEqual(len(r), day_seconds)
            self.assertEqual(r.start.weekday, iso, r.start.weekday)
            self.assertEqual(r.end.weekday, iso % 7 + 1, r.end.weekday)
            d = Date(day_name)
            self.assertTrue(d in r, '%s: %s' % (d, r))

        for name, iso in WEEKDAY_ORDINALS_DE.items():
            test_weekday(name, iso)

    def test_relative_day_de(self):
        for day_name, offset in RELATIVE_DAYS_DE.items():
            self.assert_range(day_name,
                              datetime(2017, 6, 16 + offset),
                              datetime(2017, 6, 16 + offset + 1))

    def test_time_formats_de(self):
        for time_str in ['22 uhr', 'um 22 uhr']:  # TODO 22h00
            self.assert_range(time_str,
                              datetime(2017, 6, 16, 22),
                              datetime(2017, 6, 16, 23))

        for time_str in ['um 19 uhr 30', '19 uhr 30', 'um 19h30', '19h30']:
            self.assert_range(time_str,
                              datetime(2017, 6, 16, 19, 30),
                              datetime(2017, 6, 16, 19, 31))

        for time_str in ['um 19 uhr 30', '19 uhr 30', 'um 19h30', '19h30']:
            self.assert_range('morgen ' + time_str,
                              datetime(2017, 6, 17, 19, 30),
                              datetime(2017, 6, 17, 19, 31))


def main():
    os.environ['TZ'] = 'UTC'
    time.tzset()
    unittest.main()


if __name__ == '__main__':
    main()
