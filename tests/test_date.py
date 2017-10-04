from datetime import datetime, timedelta
import os
import time
import unittest

from freezegun import freeze_time

from timestring import Date
from timestring.Date import WEEKDAY_ORDINALS_DE, RELATIVE_DAYS_DE


@freeze_time('2017-06-16 19:37:22')
class DateTest(unittest.TestCase):
    def assert_date(self, date_str, expected: datetime):
        _date = Date(date_str)

        self.assertEqual(_date,
                         expected,
                         '\n    Text: ' + date_str
                         + '\nExpected: ' + str(expected)
                         + '\n  Actual: ' + str(_date))

    def test_time_formats(self):
        self.assert_date('november 5 @ 10pm', datetime(2017, 11, 5, 22, 0, 0))

        for time_str in ['11am', '11 AM', '11a', "11 o'clock", "11 oclock",]:
            self.assert_date(time_str, datetime(2017, 6, 16, 11, 0, 0))
            # TODO: at 11
            # TODO: eleven o'clock
            # TODO: 1100 hours
            # TODO: by
            # TODO: dec 31 11pm
            # TODO: dec 31, 11pm
            # TODO: dec 31 11pm
            # TODO: 11pm, dec 31
            # TODO: dec 31 @ 11pm

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

    def test_in(self):  # Same as "from now"
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

    def test_weekdays_de(self):
        now = datetime.now()

        def test_weekday(day_name, iso):
            self.assert_date(day_name, datetime(2017, 6, 17 + (iso + 1) % 7)),
            d = Date(day_name)
            self.assertLess(d.date - now, timedelta(days=7), day_name)
            self.assertEqual(d.weekday, iso, day_name)

        for name, iso in WEEKDAY_ORDINALS_DE.items():
            test_weekday(name, iso)

        d = Date('jetzt')
        self.assertEqual(d, datetime(2017, 6, 16, 19, 37, 22))

    def test_relative_day_de(self):
        for day_name, offset in RELATIVE_DAYS_DE.items():
            self.assert_date(day_name,
                             datetime(2017, 6, 16 + offset))

    def test_time_formats_de(self):
        for time_str in ['22 uhr', 'um 22 uhr', '22h00']:
            self.assert_date(time_str, datetime(2017, 6, 16, 22))

        for time_str in ['um 19 uhr 30', '19 uhr 30', 'um 19h30', '19h30']:
            self.assert_date(time_str, datetime(2017, 6, 16, 19, 30))

        for time_str in ['um 19 uhr 30', '19 uhr 30', 'um 19h30', '19h30']:
            self.assert_date('morgen ' + time_str,
                             datetime(2017, 6, 17, 19, 30))

def main():
    os.environ['TZ'] = 'UTC'
    time.tzset()
    unittest.main()


if __name__ == '__main__':
    main()
