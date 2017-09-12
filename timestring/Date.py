import re
import time
import pytz
import math
from copy import copy
from datetime import datetime, timedelta

from timestring.text2num import text2num
from timestring import TimestringInvalid
from timestring.timestring_re import TIMESTRING_RE
from timestring.utils import get_timezone_time

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


class Date(object):
    def __init__(self, date=None, offset=None, start_of_week=None, tz=None, verbose=False):
        self._original = date
        if tz:
            tz = pytz.timezone(str(tz))
        else:
            tz = None

        if isinstance(date, Date):
            self.date = copy(date.date)

        elif isinstance(date, datetime):
            self.date = date

        elif isinstance(date, (int, long, float)) \
                    or (isinstance(date, (str, unicode)) and date.isdigit()) \
                and len(str(int(float(date)))) > 4:
            self.date = datetime.fromtimestamp(int(date))

        elif date == 'now' or date is None:
            self.date = datetime.now(tz)

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

            # TODO Refactor
            if isinstance(date, dict):  # This will always be True
                now = datetime.now(tz)
                new_date = copy(now)
                delta = date.get('delta') or date.get('delta_2')
                num = date.get('num')
                ref = date.get('ref')

                if date.get('unixtime'):
                    new_date = datetime.fromtimestamp(int(date.get('unixtime')))

                # Number of (days|...) [ago]
                elif num and delta:
                    delta = delta.lower()

                    sign = -1 if date.get('ago', True) or ref == 'last' else 1
                    if 'couple' in (num or ''):
                        mag = 2
                    else:
                        mag = int(text2num(num or 'one'))

                    i = sign * mag

                    if delta.startswith('y'):
                        try:
                            new_date = new_date.replace(year=new_date.year + i)
                        except ValueError:  # Leap date in a non-leap year
                            new_date += timedelta(days=365 * i)
                    elif delta.startswith('month'):
                        try:
                            new_date = new_date.replace(month=new_date.month + i)
                        except ValueError:  # No such day in that month
                            new_date += timedelta(days=30 * i)

                    elif delta.startswith('q'):
                        # TODO This section is not working
                        q1, q2, q3, q4 = datetime(new_date.year, 1, 1), datetime(new_date.year, 4, 1), datetime(new_date.year, 7, 1), datetime(new_date.year, 10, 1)
                        if q1 <= new_date < q2:
                            # We are in Q1
                            if i == -1:
                                new_date = datetime(new_date.year-1, 10, 1)
                            else:
                                new_date = q2
                        elif q2 <= new_date < q3:
                            # We are in Q2
                            pass
                        elif q3 <= new_date < q4:
                            # We are in Q3
                            pass
                        else:
                            # We are in Q4
                            pass
                        new_date += timedelta(days= 91 * i)

                    elif delta.startswith('w'):
                        new_date += timedelta(days=i * 7)
                    elif delta.startswith('d'):
                        new_date += timedelta(days=i)
                    elif delta.startswith('h'):
                        new_date += timedelta(hours=i)
                    elif delta.startswith('m'):
                        new_date += timedelta(minutes=i)
                    elif delta.startswith('s'):
                        new_date += timedelta(seconds=i)


                # !dow
                dow = next((date.get(key) for key in ('day', 'day_2', 'day_3')
                           if date.get(key)),
                          None)
                if dow is not None:
                    new_date.replace(hour=0, minute=0, second=0, microsecond=0)
                    iso = WEEKDAY_ORDINALS.get(dow)
                    if iso:
                        # Determine direction
                        if ref in ['next', 'upcoming']:
                            days = iso - new_date.isoweekday() + (7 if iso <= new_date.isoweekday() else 0)
                        elif ref in ['last', 'previous', 'prev']:
                            days = iso - new_date.isoweekday() - (7 if iso >= new_date.isoweekday() else 0)
                        else:
                            days = iso - new_date.isoweekday() + (7 if iso < new_date.isoweekday() else 0)
                        new_date = new_date + timedelta(days=days)
                    else:
                        if dow == 'yesterday':
                            new_date = new_date - timedelta(days=1)
                        elif dow == 'tomorrow':
                            new_date = new_date + timedelta(days=1)
                        elif dow == 'day before yesterday':
                            new_date = new_date - timedelta(days=2)
                        elif dow == 'day after tomorrow':
                            new_date = new_date + timedelta(days=2)

                # !year
                year = [int(CLEAN_NUMBER.sub('', date[key])) for key in ('year', 'year_2', 'year_3', 'year_4', 'year_5', 'year_6') if date.get(key)]
                if year:
                    if ref:
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
                    if ref in ['next', 'upcoming']:
                        if month_ord <= now.month:
                            new_date = new_date.replace(year=new_date.year + 1)
                    elif ref in ['last', 'previous', 'prev']:
                        if month_ord >= now.month:
                            new_date = new_date.replace(year=new_date.year - 1)
                    elif month_ord < now.month and not year:
                        new_date = new_date.replace(year=new_date.year + 1)

                # !day
                day = [date.get(key) for key in ('date', 'date_2', 'date_3', 'date_4') if date.get(key)]
                if day:
                    if ref:
                        TimestringInvalid('"next" %s'% day)
                    new_date = new_date.replace(day=int(max(day)))

                # !daytime
                daytime = date.get('daytime')
                if daytime:
                    if daytime.find('this time') >= 1:
                        current_time = get_timezone_time(tz)
                        new_date = new_date.replace(hour= current_time.hour,
                                                    minute=current_time.minute)
                    else:
                        new_date = new_date.replace(hour=dict(morning=9, noon=12, afternoon=15, evening=18, night=21, nighttime=21, midnight=24).get(date.get('daytime'), 12))
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

                    #minute
                    minute = [date.get(key) for key in ('minute', 'minute_2') if date.get(key)]
                    if minute:
                        new_date = new_date.replace(minute=int(max(minute)))

                    #second
                    seconds = date.get('seconds', 0)
                    if seconds:
                        new_date = new_date.replace(second=int(seconds))

                if year != [] and not month and dow is None and not day:
                    new_date = new_date.replace(month=1)
                if (year != [] or month) and dow is None and not (day or hour):
                    new_date = new_date.replace(day=1)
                if not hour and daytime is None and not delta:
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
    def year(self, year):
        self.date = self.date.replace(year=year)

    @property
    def month(self):
        if self.date != 'infinity':
            return self.date.month

    @month.setter
    def month(self, month):
        self.date = self.date.replace(month=month)

    @property
    def day(self):
        if self.date != 'infinity':
            return self.date.day

    @day.setter
    def day(self, day):
        self.date = self.date.replace(day=day)

    @property
    def hour(self):
        if self.date != 'infinity':
            return self.date.hour

    @hour.setter
    def hour(self, hour):
        self.date = self.date.replace(hour=hour)

    @property
    def minute(self):
        if self.date != 'infinity':
            return self.date.minute

    @minute.setter
    def minute(self, minute):
        self.date = self.date.replace(minute=minute)

    @property
    def second(self):
        if self.date != 'infinity':
            return self.date.second

    @second.setter
    def second(self, second):
        self.date = self.date.replace(second=second)

    @property
    def microsecond(self):
        if self.date != 'infinity':
            return self.date.microsecond

    @microsecond.setter
    def microsecond(self, microsecond):
        self.date = self.date.replace(microsecond=microsecond)

    @property
    def weekday(self):
        if self.date != 'infinity':
            return self.date.isoweekday()

    @property
    def tz(self):
        if self.date != 'infinity':
            return self.date.tzinfo

    @tz.setter
    def tz(self, tz):
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

    def adjust(self, to):
        '''
        Adjusts the time from kwargs to timedelta
        **Will change this object**

        return new copy of self
        '''
        if self.date == 'infinity':
            return
        new = copy(self)
        if type(to) in (str, unicode):
            to = to.lower()
            res = TIMESTRING_RE.search(to)
            if res:
                rgroup = res.groupdict()
                if (rgroup.get('delta') or rgroup.get('delta_2')):
                    i = int(text2num(rgroup.get('num', 'one'))) * (-1 if to.startswith('-') else 1)
                    delta = (rgroup.get('delta') or rgroup.get('delta_2')).lower()
                    if delta.startswith('y'):
                        try:
                            new.date = new.date.replace(year=(new.date.year + i))
                        except ValueError:
                            # day is out of range for month
                            new.date = new.date + timedelta(days=(365 * i))
                    elif delta.startswith('month'):
                        if (new.date.month + i) > 12:
                            month = (new.date.month + i) % 12
                            year = math.floor((new.date.month + i)/12)
                            new.date = new.date.replace(month=month, year=new.date.year+year)
                        elif (new.date.month + i) < 1:
                            month = (new.date.month+i) % 12   # current= jan (1), i = -3, month = (1-3)%12 = 10
                            if month == 0:
                                month = new.date.month
                            year = int((-1*(new.date.month+i))/12) + 1    #1 is added to fix 0 case
                            new.date = new.date.replace(month=month, year=(new.date.year - year))
                        else:
                            new.date = new.date.replace(month=(new.date.month + i))
                    elif delta.startswith('q'):
                        # NP
                        pass
                    elif delta.startswith('w'):
                        new.date = new.date + timedelta(days=(7 * i))
                    elif delta.startswith('s'):
                        new.date = new.date + timedelta(seconds=i)
                    else:
                        new.date = new.date + timedelta(**{('days' if delta.startswith('d') else 'hours' if delta.startswith('h') else 'minutes' if delta.startswith('m') else 'seconds'): i})
                    return new
        else:
            new.date = new.date + timedelta(seconds=int(to))
            return new

        raise TimestringInvalid('Invalid addition request')

    def __nonzero__(self):
        return True

    def __add__(self, to):
        if self.date == 'infinity':
            return copy(self)
        return copy(self).adjust(to)

    def __sub__(self, to):
        if self.date == 'infinity':
            return copy(self)
        if type(to) in (str, unicode):
            to = to[1:] if to.startswith('-') else ('-'+to)
        elif type(to) in (int, float, long):
            to = to * -1
        return copy(self).adjust(to)

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
