import re
import time
from copy import copy
from datetime import datetime, timedelta
from typing import Union

import pytz

from timestring import TimestringInvalid, Context
from .timestring_re import TIMESTRING_RE
from .utils import get_num

try:
    unicode
except NameError:
    unicode = str
    long = int

CLEAN_NUMBER = re.compile(r"[\D]")
MONTH_ORDINALS = dict(
    january=1, february=2, march=3, april=4, june=6,
    july=7, august=8, september=9, october=10, november=11, december=12,
    jan=1, feb=2, mar=3, apr=4, may=5, jun=6,
    jul=7, aug=8, sep=9, sept=9, oct=10, nov=11, dec=12,
)
WEEKDAY_ORDINALS = dict(
    monday=1, tuesday=2, wednesday=3, thursday=4, friday=5, saturday=6, sunday=7,
    mon=1, tue=2, tues=2, wed=3, wedn=3, thu=4, thur=4, fri=5, sat=6, sun=7,
    mo=1, tu=2, we=3, th=4, fr=5, sa=6, su=7,
)
RELATIVE_DAYS = {
    'now': 0,
    'today': 0,
    'yesterday': -1,
    'tomorrow': 1,
    'day before yesterday': -2,
    'day after tomorrow': 2,
}
DAYTIMES = dict(
    morning=9,
    noon=12,
    afternoon=15,
    evening=18,
    night=21,
    nighttime=21,
    midnight=24
)
TIMEDELTA_UNITS = dict(
    w='weeks',
    d='days',
    h='hours',
    m='minutes',
    s='seconds',
    u='microseconds',
)


class Date(object):
    def __init__(self, date=None, offset: dict = None, tz: str = None,
                 now: datetime = None, verbose=False, context=None):
        self._original = date
        if tz:
            tz = pytz.timezone(str(tz))
        else:
            tz = None

        if not now:
            now = datetime.now(tz)

        if isinstance(date, Date):
            self.date = copy(date.date)

        elif isinstance(date, datetime):
            self.date = date

        elif isinstance(date, (int, long, float)) \
                    or (isinstance(date, (str, unicode)) and date.isdigit()) \
                and len(str(int(float(date)))) > 4:
            self.date = datetime.fromtimestamp(int(date))

        elif date == 'now' or date is None:
            self.date = now

        elif date == 'infinity':
            self.date = 'infinity'

        elif isinstance(date, (str, unicode)) and re.match(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d+-\d{2}", date):
            self.date = datetime.strptime(date[:-3], "%Y-%m-%d %H:%M:%S.%f") - timedelta(hours=int(date[-3:]))

        elif isinstance(date, (str, unicode, dict)):
            if type(date) in (str, unicode):
                # Convert the string to a dict
                _date = date.lower()
                res = TIMESTRING_RE.search(_date.strip())

                if res:
                    date = res.groupdict()
                    if verbose:
                        print("Matches:\n", ''.join(["\t%s: %s\n" % (k, v) for k, v in date.items() if v]))
                else:
                    raise TimestringInvalid('Invalid date string: %s' % date)

                date = dict((k, v if type(v) is str else v) for k, v in date.items() if v)

            new_date = copy(now)

            # TODO Refactor
            if isinstance(date, dict):  # This will always be True
                unit = date.get('delta') or date.get('delta')
                num = date.get('num')

                if date.get('unixtime'):
                    new_date = datetime.fromtimestamp(int(date.get('unixtime')))

                # Number of (days|...) [ago]
                elif num and unit:
                    unit = unit.lower()
                    if date.get('ago') or context == Context.PREV or date.get('prev'):
                        sign = -1
                    elif date.get('in') or date.get('from_now') or context == Context.NEXT or date.get('next'):
                        sign = 1
                    else:
                        raise TimestringInvalid('Missing relationship such as "ago" or "from now"')

                    new_date = Date(new_date).plus_(num, unit, sign).date

                elif date.get('workday'):
                    new_date = new_date.replace(hour=0, minute=0, second=0, microsecond=0)
                    num = get_num(num or 1)
                    if context == Context.PREV or date.get('prev') or date.get('ago'):
                        sign = -1
                    else:
                        sign = 1
                    wd = new_date.weekday()
                    days = 0
                    i = 0
                    while i < num:
                        days += sign
                        if (wd + days) % 7 not in [5, 6]:
                            i += 1
                    new_date += timedelta(days=days)

                weekday = date.get('weekday')
                relative_day = date.get('relative_day')
                if weekday:
                    new_date = new_date.replace(hour=0, minute=0, second=0, microsecond=0)
                    iso = WEEKDAY_ORDINALS.get(weekday)
                    if iso is not None:
                        days = iso - new_date.isoweekday()
                        if date.get('prev') or context == Context.PREV:
                            if iso >= new_date.isoweekday():
                                days -= 7
                        elif not (days == 0 and context in [Context.PAST, Context.FUTURE]):
                            if iso <= new_date.isoweekday():
                                days += 7
                        new_date += timedelta(days=days)
                elif relative_day:
                    days = RELATIVE_DAYS.get(re.sub(r'\s+', ' ', relative_day))
                    if days:
                        new_date += timedelta(days=days)
                    new_date = new_date.replace(hour=0, minute=0, second=0, microsecond=0)

                # !year
                year = [int(CLEAN_NUMBER.sub('', date[key])) for key in ('year', 'year_2', 'year_3', 'year_4', 'year_5', 'year_6') if date.get(key)]
                if year:
                    if date.get('recurrence'):
                        TimestringInvalid('"next" %s'% year)
                    year = max(year)
                    if len(str(year)) != 4:
                        year += 2000 if year <= 40 else 1900
                    new_date = new_date.replace(year=year)

                # !month
                month = [date.get(key) for key in ('month', 'month_1', 'month_2', 'month_3', 'month_4', 'month_5') if date.get(key)]
                if month:
                    month_ = max(month)
                    if month_.isdigit():
                        month_ord = int(month_)
                        if not 1 <= month_ord <= 12:
                            raise TimestringInvalid('Month not in range 1..12:' + month_)
                    else:
                        month_ord = MONTH_ORDINALS.get(month_, new_date.month)

                    new_date = new_date.replace(month=int(month_ord))

                    if year == []:
                        if date.get('next') or context == Context.NEXT:
                            if month_ord <= now.month:
                                new_date = new_date.replace(year=new_date.year + 1)
                        elif date.get('prev') or context == Context.PREV:
                            if month_ord >= now.month:
                                new_date = new_date.replace(year=new_date.year - 1)
                        elif month_ord < now.month and not year:
                            new_date = new_date.replace(year=new_date.year + 1)

                # !day
                day = [date.get(key) for key in ('date', 'date_2', 'date_3', 'date_4') if date.get(key)]
                if day:
                    if date.get('recurrence'):
                        TimestringInvalid('"next" %s'% day)
                    new_date = new_date.replace(day=int(max(day)))

                # !daytime
                daytime = date.get('daytime')
                if daytime:
                    if 'this time' not in daytime:
                        _hour = DAYTIMES.get(date.get('daytime'), 12)
                        new_date = new_date.replace(hour=_hour,
                                                    minute=0,
                                                    second=0,
                                                    microsecond=0)
                    # No offset because the hour was set.
                    offset = False

                # !hour
                hour = [date.get(key) for key in ('hour', 'hour_2', 'hour_3') if date.get(key)]
                if hour:
                    new_date = new_date.replace(hour=int(max(hour)), minute=0, second=0)
                    am = [date.get(key) for key in ('am', 'am_1') if date.get(key)]
                    if am and max(am) in ('p', 'pm'):
                        h = int(max(hour))
                        if h < 12:
                            new_date = new_date.replace(hour=h+12)
                    # No offset because the hour was set.
                    offset = False

                    minute = [date.get(key) for key in ('minute', 'minute_2') if date.get(key)]
                    if minute:
                        new_date = new_date.replace(minute=int(max(minute)))

                    seconds = date.get('seconds', 0)
                    if seconds:
                        new_date = new_date.replace(second=int(seconds))

                    new_date = new_date.replace(microsecond=0)

                    if not day and not relative_day and new_date < now:
                        new_date += timedelta(days=1)

                if year != [] and not month and weekday is None and not day:
                    new_date = new_date.replace(month=1)
                if (year != [] or month) and weekday is None and not (day or hour):
                    new_date = new_date.replace(day=1)
                if not hour and daytime is None and not unit:
                    new_date = new_date.replace(hour=0, minute=0, second=0)

            self.date = new_date

        else:
            raise TimestringInvalid('Invalid type for constructing Date')

        if offset and isinstance(offset, dict):
            self.date = self.date.replace(**offset)

    def __repr__(self):
        return "<timestring.Date %s %s>" % (str(self), id(self))

    @property
    def year(self):
        if self.date != 'infinity':
            return self.date.year

    @year.setter
    def year(self, year: int):
        self.date = self.date.replace(year=year)

    @property
    def month(self):
        if self.date != 'infinity':
            return self.date.month

    @month.setter
    def month(self, month: int):
        self.date = self.date.replace(month=month)

    @property
    def day(self):
        if self.date != 'infinity':
            return self.date.day

    @day.setter
    def day(self, day: int):
        self.date = self.date.replace(day=day)

    @property
    def hour(self):
        if self.date != 'infinity':
            return self.date.hour

    @hour.setter
    def hour(self, hour: int):
        self.date = self.date.replace(hour=hour)

    @property
    def minute(self):
        if self.date != 'infinity':
            return self.date.minute

    @minute.setter
    def minute(self, minute: int):
        self.date = self.date.replace(minute=minute)

    @property
    def second(self):
        if self.date != 'infinity':
            return self.date.second

    @second.setter
    def second(self, second: int):
        self.date = self.date.replace(second=second)

    @property
    def microsecond(self):
        if self.date != 'infinity':
            return self.date.microsecond

    @microsecond.setter
    def microsecond(self, microsecond: int):
        self.date = self.date.replace(microsecond=microsecond)

    @property
    def isoweekday(self):
        if self.date != 'infinity':
            return self.date.isoweekday()

    @property
    def weekday(self):
        if self.date != 'infinity':
            return self.date.weekday()

    @property
    def tz(self):
        if self.date != 'infinity':
            return self.date.tzinfo

    @tz.setter
    def tz(self, tz: str):
        if self.date != 'infinity':
            if tz is None:
                self.date = self.date.replace(tzinfo=None)
            else:
                self.date = self.date.replace(tzinfo=pytz.timezone(tz))

    def replace(self, **k):
        """Note returns a new Date obj"""
        if self.date != 'infinity':
            return Date(self.date.replace(**k))
        else:
            return Date('infinity')

    def plus_(self, num: Union[str, int, float], unit: str, sign: int = 1):
        assert sign in [-1, 1]
        mag = get_num(num)
        n = sign * mag
        whole = int(n)
        fraction = n - whole

        unit = unit.lower().strip()
        new_date = copy(self.date)
        if unit.startswith('y'):
            try:
                new_date = new_date.replace(year=new_date.year + whole)
                new_date += timedelta(days=365 * fraction)
            except ValueError:  # Leap date in a non-leap year
                new_date += timedelta(days=365 * n)
        elif unit.startswith('month'):
            try:
                month = new_date.month + whole
                new_date = new_date.replace(
                    year=new_date.year + month // 12,
                    month=abs(month) % 12
                )
                new_date += timedelta(days=30 * fraction)
            except ValueError:  # No such day in that month
                new_date += timedelta(days=30 * n)

        elif unit.startswith('q'):
            # TODO This section is not working
            q1 = datetime(new_date.year, 1, 1)
            q2 = datetime(new_date.year, 4, 1)
            q3 = datetime(new_date.year, 7, 1)
            q4 = datetime(new_date.year, 10, 1)
            if q1 <= new_date < q2:
                if n == -1:
                    new_date = datetime(new_date.year - 1, 10, 1)
                else:
                    new_date = q2
            elif q2 <= new_date < q3:
                pass
            elif q3 <= new_date < q4:
                pass
            else:
                pass
            new_date += timedelta(days=91 * n)

        else:
            _unit = TIMEDELTA_UNITS.get(unit[0])
            if _unit:
                new_date += timedelta(**{_unit: n})
            else:
                raise TimestringInvalid('Unknown time unit: ' + unit)

        return Date(new_date)

    def plus(self, duration: Union[str, int, float, timedelta]):
        """
        :return a new Date adjusted by the duration
        :param duration: int or float number of seconds or string of number and
         time unit. The number can begin with '-' to indicate subtraction
        """
        if self.date == 'infinity':
            return
        if isinstance(duration, timedelta):
            return Date(self.date + duration)
        if isinstance(duration, (str, unicode)):
            duration = duration.lower().strip()
            res = TIMESTRING_RE.search(duration)
            if res:
                res = res.groupdict()
            sign = -1 if duration.startswith('-') else 1
            num = res.get('num')
            unit = res.get('delta') or res.get('delta_2')
            return self.plus_(num, unit, sign)
        elif isinstance(duration, (float, int)):
            new = copy(self)
            new.date = new.date + timedelta(seconds=duration)
            return new

        raise TimestringInvalid('Invalid type for plus(): %s'
                                % (type(duration)))

    def __nonzero__(self):
        return True

    def __add__(self, duration: Union[str, int, float, timedelta]):
        if self.date == 'infinity':
            return copy(self)
        return self.plus(duration)

    def __sub__(self, other):
        if isinstance(other, timedelta):
            return Date(self.date - other)
        if self.date == 'infinity':
            return copy(self)
        if isinstance(other, (str, unicode)):
            other = other[1:] if other.startswith('-') else ('-' + other)
        elif type(other) in (int, float, long):
            other *= -1
        return self.plus(other)

    def __format__(self, _):
        if self.date != 'infinity':
            return self.date.strftime('%x %X')
        else:
            return 'infinity'

    def __str__(self):
        """Returns date in representation of `%x %X` ie `2013-02-17 00:00:00`"""
        return str(self.date)

    def __gt__(self, other):
        if self.date == 'infinity':
            if isinstance(other, Date):
                return other.date != 'infinity'
            else:
                from .Range import Range
                if isinstance(other, Range):
                    return other.end != 'infinity'
                return other != 'infinity'
        else:
            if isinstance(other, Date):
                if other.date == 'infinity':
                    return False
                elif other.tz and self.tz is None:
                    return self.date.replace(tzinfo=other.tz) > other.date
                elif self.tz and other.tz is None:
                    return self.date > other.date.replace(tzinfo=self.tz)
                return self.date > other.date
            else:
                from .Range import Range
                if isinstance(other, Range):
                    if other.end.date == 'infinity':
                        return False
                    if other.end.tz and self.tz is None:
                        return self.date.replace(tzinfo=other.end.tz) > other.end.date
                    elif self.tz and other.end.tz is None:
                        return self.date > other.end.date.replace(tzinfo=self.tz)
                    return self.date > other.end.date
                else:
                    return self.__gt__(Date(other, tz=self.tz))

    def __lt__(self, other):
        if self.date == 'infinity':
            # infinity can never by less then a date
            return False

        if isinstance(other, Date):
            if other.date == 'infinity':
                return True
            elif other.tz and self.tz is None:
                return self.date.replace(tzinfo=other.tz) < other.date
            elif self.tz and other.tz is None:
                return self.date < other.date.replace(tzinfo=self.tz)
            return self.date < other.date
        else:
            from .Range import Range
            if isinstance(other, Range):
                if other.end.tz and self.tz is None:
                    return self.date.replace(tzinfo=other.end.tz) < other.end.date
                elif self.tz and other.end.tz is None:
                    return self.date < other.end.date.replace(tzinfo=self.tz)
                return self.date < other.end.date
            else:
                return self.__lt__(Date(other, tz=self.tz))

    def __ge__(self, other):
        return self > other or self == other

    def __le__(self, other):
        return self < other or self == other

    def __eq__(self, other):
        if isinstance(other, datetime):
            other = Date(other)
        if isinstance(other, Date):
            if other.date == 'infinity':
                return self.date == 'infinity'

            elif other.tz and self.tz is None:
                return self.date.replace(tzinfo=other.tz) == other.date

            elif self.tz and other.tz is None:
                return self.date == other.date.replace(tzinfo=self.tz)

            return self.date == other.date
        else:
            from .Range import Range
            if isinstance(other, Range):
                return False
            else:
                return self.__eq__(Date(other, tz=self.tz))

    def __ne__(self, other):
        return not self.__eq__(other)

    def format(self, format_string='%x %X'):
        if self.date != 'infinity':
            return self.date.strftime(format_string)
        else:
            return 'infinity'

    def to_unixtime(self):
        if self.date != 'infinity':
            return time.mktime(self.date.timetuple())
        else:
            return -1
