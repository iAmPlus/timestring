import os
import time
import unittest
from ddt import ddt, data
from six import u
from datetime import datetime, timedelta

from freezegun import freeze_time
import pytest

from timestring import Date, Range, parse, TimestringInvalid
from timestring.text2num import text2num
from timestring.timestring_re import TIMESTRING_RE as ts


@freeze_time('2017-06-16 19:37:22')
@ddt
class T(unittest.TestCase):
    def assert_date(self, date_str, expected: datetime):
        actual = Date(date_str)

        self.assertEqual(actual,
                         expected,
                         '\n    Text: ' + date_str
                         + '\nExpected: ' + str(expected)
                         + '\n  Actual: ' + str(actual))

    def test_fullstring(self):
        now = datetime.now()

        #
        # DATE
        #
        date = Date("01/10/2015 at 7:30pm")
        self.assertEqual(date.year, 2015)
        self.assertEqual(date.month, 1)
        self.assertEqual(date.day, 10)
        self.assertEqual(date.hour, 19)
        self.assertEqual(date.minute, 30)

        date = Date("may 23rd, 1988 at 6:24 am")
        self.assertEqual(date.year, 1988)
        self.assertEqual(date.month, 5)
        self.assertEqual(date.day, 23)
        self.assertEqual(date.hour, 6)
        self.assertEqual(date.minute, 24)

        date = Date('2012 feb 2 1:13PM')
        self.assertEqual(date.year, 2012)
        self.assertEqual(date.month, 2)
        self.assertEqual(date.day, 2)
        self.assertEqual(date.hour, 13)
        self.assertEqual(date.minute, 13)

        date = Date('6:41 am on sept 8 2012')
        self.assertEqual(date.year, 2012)
        self.assertEqual(date.month, 9)
        self.assertEqual(date.day, 8)
        self.assertEqual(date.hour, 6)
        self.assertEqual(date.minute, 41)


        #
        # RANGE
        #
        r = Range('From 04/17/13 04:18:00 to 05/01/13 17:01:00', tz='US/Central')
        self.assertEqual(r.start.year, 2013)
        self.assertEqual(r.start.month, 4)
        self.assertEqual(r.start.day, 17)
        self.assertEqual(r.start.hour, 4)
        self.assertEqual(r.start.minute, 18)
        self.assertEqual(r.end.year, 2013)
        self.assertEqual(r.end.month, 5)
        self.assertEqual(r.end.day, 1)
        self.assertEqual(r.end.hour, 17)
        self.assertEqual(r.end.minute, 1)

        date = Date('2013-09-10T10:45:50')
        self.assertEqual(date.year, 2013)
        self.assertEqual(date.month, 9)
        self.assertEqual(date.day, 10)
        self.assertEqual(date.hour, 10)
        self.assertEqual(date.minute, 45)
        self.assertEqual(date.second, 50)

        _range = Range('tomorrow 10am to 5pm')
        tomorrow = now + timedelta(days=1)
        self.assertEqual(_range.start.year, tomorrow.year)
        self.assertEqual(_range.end.year, tomorrow.year)
        self.assertEqual(_range.start.month, tomorrow.month)
        self.assertEqual(_range.end.month, tomorrow.month)
        self.assertEqual(_range.start.day, tomorrow.day)
        self.assertEqual(_range.end.day, tomorrow.day)
        self.assertEqual(_range.start.hour, 10)
        self.assertEqual(_range.end.hour, 17)

    def test_dates(self):
        date = Date("August 25th, 2014 12:30 PM")
        [self.assertEqual(*m) for m in ((date.year, 2014), (date.month, 8), (date.day, 25), (date.hour, 12), (date.minute, 30), (date.second, 0))]

        date = Date("may 23, 2018 1 pm")
        [self.assertEqual(*m) for m in ((date.year, 2018), (date.month, 5), (date.day, 23), (date.hour, 13), (date.minute, 0), (date.second, 0))]

        date = Date("1-2-13 2 am")
        [self.assertEqual(*m) for m in ((date.year, 2013), (date.month, 1), (date.day, 2), (date.hour, 2), (date.minute, 0), (date.second, 0))]

        date = Date("dec 15th '01 at 6:25:01 am")
        [self.assertEqual(*m) for m in ((date.year, 2001), (date.month, 12), (date.day, 15), (date.hour, 6), (date.minute, 25), (date.second, 1))]

    def test_singles(self):
        now = datetime.now()
        #
        # Single check
        #
        self.assertEqual(Date("2012").year, 2012)
        self.assertEqual(Date("January 2013").month, 1)
        self.assertEqual(Date("feb 2011").month, 2)
        self.assertEqual(Date("05/23/2012").month, 5)
        self.assertEqual(Date("01/10/2015 at 7:30pm").month, 1)
        self.assertEqual(Date("today").day, now.day)

        range = Range('january')
        self.assertEqual(range[0].month, 1)
        self.assertEqual(range[0].day, 1)
        self.assertEqual(range[0].hour, 0)
        self.assertEqual(range[1].month, 2)
        self.assertEqual(range[1].day, 1)
        self.assertEqual(range[1].hour, 0)
        range = Range('December')
        self.assertEqual(range[0].month, 12)
        self.assertEqual(range[0].day, 1)
        self.assertEqual(range[0].hour, 0)
        self.assertEqual(range[1].month, 1)
        self.assertEqual(range[1].day, 1)
        self.assertEqual(range[1].hour, 0)
        range = Range('2010')
        self.assertEqual(range[0].year, 2010)
        self.assertEqual(range[0].month, 1)
        self.assertEqual(range[0].day, 1)
        self.assertEqual(range[0].hour, 0)
        self.assertEqual(range[1].year, 2011)
        self.assertEqual(range[1].month, 1)
        self.assertEqual(range[1].day, 1)
        self.assertEqual(range[1].hour, 0)
        range = Range('january 2011')
        self.assertEqual(range[0].year, 2011)
        self.assertEqual(range[0].month, 1)
        self.assertEqual(range[0].day, 1)
        self.assertEqual(range[0].hour, 0)
        self.assertEqual(range[1].year, 2011)
        self.assertEqual(range[1].month, 2)
        self.assertEqual(range[1].day, 1)
        self.assertEqual(range[1].hour, 0)

        date = Date(1374681560)
        self.assertEqual(date.year, 2013)
        self.assertEqual(date.month, 7)
        self.assertEqual(date.day, 24)
        date = Date('1374681560')
        self.assertEqual(date.year, 2013)
        self.assertEqual(date.month, 7)
        self.assertEqual(date.day, 24)
        range = Range(1374681560)
        self.assertEqual(range.start.day, 24)
        self.assertEqual(range.end.day, 24)

        # offset timezones
        self.assertEqual(Date("2014-03-06 15:33:43.764419-05").hour, 20)

        for date in ['yestserday', 'Satruday', Exception]:
            with pytest.raises(TimestringInvalid, message=str(date)):
                Date(date)

            with pytest.raises(TimestringInvalid, message=str(date)):
                Range(date)


    def test_this(self):
        now = datetime.now()

        year = Range('this year')
        self.assertEqual(year.start.year, now.year)
        self.assertEqual(year.start.month, 1)
        self.assertEqual(year.start.day, 1)
        self.assertEqual(year.start.hour, 0)
        self.assertEqual(year.start.minute, 0)
        self.assertEqual(year.end.year, now.year+1)
        self.assertEqual(year.end.month, 1)
        self.assertEqual(year.end.day, 1)
        self.assertEqual(year.end.hour, 0)
        self.assertEqual(year.end.minute, 0)
        self.assertTrue(Date('today') in year)

        # 1 year (till now)
        range = Range('1 year')
        self.assertEqual(range.start.year, now.year - 1)
        self.assertEqual(range.start.month, now.month)
        self.assertEqual(range.start.day, now.day)
        self.assertEqual(range.start.hour, now.hour)
        self.assertEqual(range.start.minute, now.minute)
        self.assertEqual(range.end.year, now.year)
        self.assertEqual(range.end.month, now.month)
        self.assertEqual(range.end.day, now.day)
        self.assertEqual(range.end.hour, now.hour)
        self.assertEqual(range.end.minute, now.minute)

        month = Range('this month')
        self.assertEqual(month.start.year, now.year)
        self.assertEqual(month.start.month, now.month)
        self.assertEqual(month.start.day, 1)
        self.assertEqual(month.start.hour, 0)
        self.assertEqual(month.start.minute, 0)
        self.assertEqual(month.end.year, month.start.year + (1 if month.start.month+1 == 13 else 0))
        self.assertEqual(month.end.month, (month.start.month + 1) if month.start.month+1 < 13 else 1)
        self.assertEqual(month.end.day, 1)
        self.assertEqual(month.end.hour, 0)
        self.assertEqual(month.end.minute, 0)

        mo = Range('this month', offset=dict(hour=6))
        self.assertEqual(mo.start.year, now.year)
        self.assertEqual(mo.start.month, now.month)
        self.assertEqual(mo.start.day, 1)
        self.assertEqual(mo.start.hour, 6)
        self.assertEqual(mo.start.minute, 0)
        self.assertEqual(mo.end.year, mo.start.year + (1 if mo.start.month+1 == 13 else 0))
        self.assertEqual(mo.end.month, (mo.start.month + 1) if mo.start.month+1 < 13 else 1)
        self.assertEqual(mo.end.day, 1)
        self.assertEqual(mo.end.hour, 6)
        self.assertEqual(mo.end.minute, 0)

        self.assertEqual(len(Range('6d')), 518400)
        self.assertEqual(len(Range('6 d')), 518400)
        self.assertEqual(len(Range('6 days')), 518400)
        self.assertEqual(len(Range('12h')), 43200)
        self.assertEqual(len(Range('6 h')), 21600)
        self.assertEqual(len(Range('10m')), 600)
        self.assertEqual(len(Range('10 m')), 600)
        self.assertEqual(len(Range('10 s')), 10)
        self.assertEqual(len(Range('10s')), 10)

    def test_dow(self):
        now = datetime.now()
        hour_in_seconds = 24 * 60 * 60
        for x, day in enumerate(('monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday')):
            d, r = Date(day), Range(day)
            self.assertLess(d.date - now, timedelta(7))
            self.assertEqual(d.weekday, 1 + x)
            self.assertEqual(len(r), hour_in_seconds)
            self.assertEqual(r.start.hour, 0)
            self.assertEqual(r.start.minute, 0)
            self.assertEqual(r.end.hour, 0)
            self.assertEqual(r.end.minute, 0)
            self.assertEqual(r.end.weekday, 1 if x+1 == 7 else (2+x))

    def test_offset(self):
        now = datetime.now()

        #
        # Offset
        #
        self.assertEqual(Date("today", offset=dict(hour=6)).hour, 6)
        self.assertEqual(Date("today", offset=dict(hour=6)).day, now.day)
        self.assertEqual(Range("this week", offset=dict(hour=10)).start.hour, 10)
        self.assertEqual(Date("yesterday", offset=dict(hour=10)).hour, 10)
        self.assertEqual(Date("august 25th 7:30am", offset=dict(hour=10)).hour, 7)

    def test_lengths(self):
        #
        # Lengths
        #
        week = 7 * 24 * 60 * 60
        self.assertEqual(len(Range("next 10 weeks")), 10 * week)
        self.assertEqual(len(Range("this week")), week)
        self.assertEqual(len(Range("3 weeks")), 3 * week)
        self.assertEqual(len(Range('yesterday')), 24 * 60 * 60)

    def test_in(self):
        self.assertTrue(Date('yesterday') in Range("last 7 days"))
        self.assertTrue(Date('today') in Range('this month'))
        self.assertTrue(Date('today') in Range('this month'))
        self.assertTrue(Range('this month') in Range('this year'))
        self.assertTrue(Range('this day') in Range('this week'))
        # these might not always be true because of end of week
        # self.assertTrue(Range('this week') in Range('this month'))
        # self.assertTrue(Range('this week') in Range('this year'))

    def test_tz(self):
        #
        # TZ
        #
        self.assertEqual(Date('today', tz="US/Central").tz.zone, 'US/Central')

    def test_cut(self):
        range_1 = Range('from january 10th 2010 to february 2nd 2010').cut('10 days')
        range_1.start.microsecond = 1
        range_1.end.microsecond = 1
        range_2 = Range('from january 10th 2010 to jan 20th 2010')
        range_2.start.microsecond = 1
        range_2.end.microsecond = 1
        self.assertEqual(range_1, range_2)

    def test_add_subtract(self):
        date_1 = Date('jan 10')
        date_1.microsecond = 1
        date_2 = Date('jan 11')
        date_2.microsecond = 1
        self.assertEqual(date_1 + '1 day', date_2)

        date_2 = Date('jan 5')
        date_2.microsecond = 1
        self.assertEqual(Date(date_1) - '5 days', date_2)

    def test_compare(self):
        self.assertFalse(Range('10 days') == Date('yesterday'))
        self.assertTrue(Date('yesterday') in Range('10 days'))
        self.assertTrue(Range('10 days') in Range('100 days'))
        self.assertTrue(Range('next 2 weeks') > Range('1 year'))
        self.assertTrue(Range('yesterday') < Range('now'))

    def test_last(self):
        now = datetime.now()

        year = Range('last year')
        self.assertEqual(year.start.year, now.year - 1)
        self.assertEqual(year.start.month, 1)
        self.assertEqual(year.start.day, 1)
        self.assertEqual(year.start.hour, 0)
        self.assertEqual(year.start.minute, 0)
        self.assertEqual(year.end.year, now.year)
        self.assertEqual(year.end.month, 1)
        self.assertEqual(year.end.day, 1)
        self.assertEqual(year.end.hour, 0)
        self.assertEqual(year.end.minute, 0)
        self.assertTrue(Date('today') not in year)

        self.assertTrue(Date('last tuesday') in Range('last 14 days'))
        self.assertTrue(Date('tuesday') in Range('next 7 days'))
        self.assertTrue(Date('next tuesday') in Range('next 14 days'))

    def test_psql_infinity(self):
        d = Date('infinity')
        self.assertTrue(d > 'now')
        self.assertTrue(d > 'today')
        self.assertTrue(d > 'next week')

        self.assertFalse(d in Range('this year'))
        self.assertFalse(d in Range('next 5 years'))

        self.assertTrue(Range('month') < d)

        r = Range('today', 'infinity')

        self.assertTrue('next 5 years' in r)
        self.assertTrue(Date('today') in r)
        self.assertTrue(d in r)
        self.assertFalse(d > r)
        self.assertFalse(r > d)

        r = Range('["2013-12-09 06:57:46.54502-05",infinity)')
        self.assertTrue(r.end == 'infinity')
        self.assertTrue('next 5 years' in r)
        self.assertTrue(Date('today') in r)
        self.assertTrue(d in r)
        self.assertFalse(d > r)
        self.assertFalse(r > d)
        self.assertEqual(r.start.year, 2013)
        self.assertEqual(r.start.month, 12)
        self.assertEqual(r.start.day, 9)
        self.assertEqual(r.start.hour, 11)
        self.assertEqual(r.start.minute, 57)
        self.assertEqual(r.start.second, 46)

    def test_date_adjustment(self):
        d = Date("Jan 1st 2014 at 10 am")
        self.assertEqual(d.year, 2014)
        self.assertEqual(d.month, 1)
        self.assertEqual(d.day, 1)
        self.assertEqual(d.hour, 10)
        self.assertEqual(d.minute, 0)
        self.assertEqual(d.second, 0)

        d.hour = 5
        d.day = 15
        d.month = 4
        d.year = 2013
        d.minute = 40
        d.second = 14
        d.microsecond = 10001

        self.assertEqual(d.year, 2013)
        self.assertEqual(d.month, 4)
        self.assertEqual(d.day, 15)
        self.assertEqual(d.hour, 5)
        self.assertEqual(d.minute, 40)
        self.assertEqual(d.second, 14)
        self.assertEqual(str(d.date), "2013-04-15 05:40:14.010001")

    def test_parse(self):
        self.assertEqual(parse('tuesday at 10pm')['hour'], 22)
        self.assertEqual(parse('tuesday at 10pm')['weekday'], 2)
        self.assertEqual(parse('may of 2014')['year'], 2014)

    @data((1, "one"),
          (12, "twelve"),
          (72, "seventy two"),
          (300, "three hundred"),
          (1200, "twelve hundred"),
          (12304, "twelve thousand three hundred four"),
          (6000000, "six million"),
          (6400005, "six million four hundred thousand five"),
          (123456789012, "one hundred twenty three billion four hundred fifty six million seven hundred eighty nine thousand twelve"),
          (4000000000000000000000000000000000, "four decillion"))
    def test_string_to_number(self, data):
        (equals, string) = data
        self.assertEqual(text2num(string), equals)
        self.assertEqual(text2num(u(string)), equals)

    def test_plus(self):
        date1 = Date("october 18, 2013 10:04:32 PM")
        date2 = date1 + "10 seconds"
        self.assertEqual(date1.second + 10, date2.second)

    def test_word_boundaries(self):
        res = ts.search("next mon")
        self.assertNotEqual(res, None)
        res = ts.search("santa monica")
        self.assertEqual(res, None)
        res = ts.search("tuesday two weeks ago")
        self.assertNotEqual(res, None)
        res = ts.search("fri")
        self.assertNotEqual(res, None)
        res = ts.search("dec")
        self.assertNotEqual(res, None)
        res = ts.search("Current weather in East hanover new jersey")
        self.assertEqual(res, None)
        res = ts.search("august")
        self.assertNotEqual(res, None)
        res = ts.search("23rd feb 9:35pm")
        self.assertNotEqual(res, None)

    def test_next_prev(self):
        # Past month
        self.assert_date('nov', datetime(2017, 11, 1))
        self.assert_date('this nov', datetime(2017, 11, 1))
        self.assert_date('last nov', datetime(2016, 11, 1))
        self.assert_date('previous nov', datetime(2016, 11, 1))
        self.assert_date('next nov', datetime(2017, 11, 1))
        self.assert_date('upcoming nov', datetime(2017, 11, 1))

        # Future month
        self.assert_date('feb', datetime(2018, 2, 1))
        self.assert_date('this feb', datetime(2018, 2, 1), )
        self.assert_date('last feb', datetime(2017, 2, 1))
        self.assert_date('previous feb', datetime(2017, 2, 1))
        self.assert_date('next feb', datetime(2018, 2, 1))
        self.assert_date('upcoming feb', datetime(2018, 2, 1))

        # Current month
        self.assert_date('june', datetime(2017, 6, 1))
        self.assert_date('this june', datetime(2017, 6, 1))
        self.assert_date('last june', datetime(2016, 6, 1))
        self.assert_date('next june', datetime(2018, 6, 1))

        # Past weekday
        self.assert_date('sun', datetime(2017, 6, 18))
        self.assert_date('this sun', datetime(2017, 6, 18))
        self.assert_date('last sun', datetime(2017, 6, 11))
        self.assert_date('previous sun', datetime(2017, 6, 11))
        self.assert_date('next sun', datetime(2017, 6, 18))
        self.assert_date('upcoming sun', datetime(2017, 6, 18))

        # Future weekday
        self.assert_date('wed', datetime(2017, 6, 21))
        self.assert_date('last wed', datetime(2017, 6, 14))
        self.assert_date('previous wed', datetime(2017, 6, 14))
        self.assert_date('next wed', datetime(2017, 6, 21))
        self.assert_date('upcoming wed', datetime(2017, 6, 21))

        # Current weekday
        self.assert_date('fri', datetime(2017, 6, 16))
        self.assert_date('this fri', datetime(2017, 6, 16))
        self.assert_date('last fri', datetime(2017, 6, 9))
        self.assert_date('next fri', datetime(2017, 6, 23))


def main():
    os.environ['TZ'] = 'UTC'
    time.tzset()
    unittest.main()


if __name__ == '__main__':
    main()
