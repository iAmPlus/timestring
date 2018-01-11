import re
from copy import copy
from datetime import datetime, timedelta
from typing import Union

import pytz

from timestring import TimestringInvalid, Context, \
    WEEKEND_START_DAY, WEEKEND_START_HOUR, WEEKEND_END_DAY, WEEKEND_END_HOUR
from .Date import Date
from .timestring_re import TIMESTRING_RE
from .utils import get_num

try:
    unicode
except NameError:
    unicode = str
    long = int

POSTGRES_DATE_PATTERN = r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}(\.\d+)?(\+|\-)\d{2}'
pg_pat_ext = r'((\"' + POSTGRES_DATE_PATTERN + '\")|infinity)'
POSTGRES_RANGE_RE = re.compile(
    r'(\[|\()' + pg_pat_ext + r',' + pg_pat_ext + r'(\]|\))'
)


class Range(object):
    def __init__(self, start: Union[int, str, long, float, datetime, Date],
                 end: Union[datetime, Date] = None, offset: dict = None,
                 week_start: int = 1, tz: str = None,
                 verbose=False, context: Context = None):
        """`start` can be type <class timestring.Date> or <type str>
        """
        self._dates = []
        pgoffset = None
        if tz:
            tz = pytz.timezone(str(tz))

        if start is None:
            raise TimestringInvalid("Range object requires a start value")

        if not isinstance(start, (Date, datetime)):
            start = str(start)
        if end and not isinstance(end, (Date, datetime)):
            end = str(end)

        if start and end:
            self._dates = (Date(start, tz=tz), Date(end, tz=tz))

        elif start == 'infinity':
            self._dates = (Date('infinity'), Date('infinity'))

        elif re.search(r'(\s(and|to)\s)', start):
            # Both sides are provided in string "start"
            start = re.sub('^(between|from)\s', '', start.lower())
            r = tuple(re.split(r'(\s(and|to)\s)', start.strip()))
            start = Date(r[0], tz=tz)
            self._dates = start, Date(r[-1], now=start.date)

        elif POSTGRES_RANGE_RE.match(start):
            # Postgresql tsrange and tstzranges support
            start, end = re.sub('[^\w\s\-\:\.\+\,]', '', start).split(',')
            self._dates = Date(start), Date(end)

        else:
            now = datetime.now(tz)

            if re.search(r"(\+|\-)\d{2}$", start):
                # postgresql tsrange and tstzranges
                pgoffset = re.search(r"(\+|\-)\d{2}$", start).group() + " hours"

            # Parse
            res = TIMESTRING_RE.search(start)
            if res:
                group = res.groupdict()

                def g(*keys):
                    return next((group.get(k) for k in keys
                                 if group.get(k) is not None),
                                None)

                if verbose:
                    print(dict(map(lambda a: (a, group.get(a)), filter(lambda a: group.get(a), group))))

                if not group['this']:
                    if group['since']:
                        context = Context.PREV
                    if group['until'] or group['by']:
                        context = Context.NEXT

                delta = group.get('delta') or group.get('delta_2')
                if delta:
                    delta = delta.lower().strip()
                    num = group['num']
                    start = Date("now", offset=offset, tz=tz)
                    end = None

                    # ago                               [     ](     )x
                    # from now                         x(     )[     ]
                    # in                               x(     )[     ]
                    if group['ago'] or group['from_now'] or group['in']:
                        n = get_num(num or 1)
                        whole = int(n)
                        fraction = n - whole
                        if verbose:
                            print('ago or from_now or in')
                        start = Date(res.string)
                        if not re.match('(hour|minute|second)s?', delta):
                            if not fraction:
                                start = start.replace(hour=0, minute=0, second=0, microsecond=0)
                            end = start.plus_(1, 'day')
                        elif delta.startswith('hour'):
                            if not fraction:
                                start = start.replace(minute=0, second=0, microsecond=0)
                            end = start + '1 hour'
                        elif delta.startswith('minute'):
                            if not fraction:
                                start = start.replace(second=0, microsecond=0)
                            end = start + '1 minute'
                        else:
                            end = start + '1 second'

                    # "next 2 weeks", "the next hour"   x[     ][     ]
                    elif group['next'] and (group['num'] or group['article']):
                        if verbose:
                            print('next and (num or article)')
                        end = start.plus_(num, delta)

                    # "next week"                       (  x  )[      ]
                    elif group['next'] or (not group['this'] and context == Context.NEXT):
                        if verbose:
                            print('next or (not this and Context.NEXT)')
                        this = Range('this ' + delta,
                                     offset=offset,
                                     tz=tz,
                                     week_start=week_start)
                        if delta.startswith('weekend'):
                            if 'now' in this:
                                start, end = this.plus_(num, delta)
                            else:
                                start, end = this
                        else:
                            start = this.end
                            end = start.plus_(num, delta)

                    # "last 2 weeks", "the last hour"   [     ][     ]x
                    elif group['prev'] and (group['num'] or group['article']):
                        if verbose:
                            print('prev and (num or article)')

                        end = start.plus_(num, delta, -1)

                    # "last week"                       [     ](  x  )
                    elif group['prev']:
                        if verbose:
                            print('prev')
                        this = Range('this ' + delta,
                                     offset=offset,
                                     tz=tz,
                                     week_start=week_start)

                        start = this.start.plus_(num, delta, -1)
                        end = this.end.plus_(num, delta, -1)

                    # "1 year", "10 days" till now
                    elif num:
                        if verbose:
                            print('num')

                        end = start.plus_(num, delta, -1)

                    # this                             [   x  ]
                    elif group['this'] or not group['recurrence']:
                        if verbose:
                            print('this or not recurrence')
                        start = Date(res.string, tz=tz)

                        if delta.startswith('y'):
                            start = start.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)

                        elif delta.startswith('mo'):
                            start = start.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

                        # weekend
                        elif delta.startswith('weekend'):
                            days = (WEEKEND_START_DAY - start.isoweekday + 7) % 7
                            start = Date(now + timedelta(days=days))
                            start = start.replace(hour=WEEKEND_START_HOUR,
                                                  minute=0,
                                                  second=0,
                                                  microsecond=0)
                            days = (WEEKEND_END_DAY + 7 - WEEKEND_START_DAY) % 7
                            end = Date(start.date + timedelta(days=days))
                            end = end.replace(hour=WEEKEND_END_HOUR)
                            start = start.replace(**offset or {})
                            end = end.replace(**offset or {})

                        # week
                        elif delta.startswith('w'):
                            start.date -= timedelta(days=start.isoweekday - week_start % 7)
                            start = start.replace(hour=0, minute=0, second=0, microsecond=0)

                        elif delta.startswith('d'):
                            start = start.replace(hour=0, minute=0, second=0, microsecond=0)

                        elif delta.startswith('h'):
                            start = start.replace(minute=0, second=0, microsecond=0)

                        elif delta.startswith('m'):
                            start = start.replace(second=0, microsecond=0)

                        elif delta.startswith('s'):
                            start = start.replace(microsecond=0)

                        else:
                            raise TimestringInvalid("Not a valid time reference")

                        if offset:
                            start = start.replace(**offset)
                        if not end:
                            end = start.plus_(num, delta)

                elif group['relative_day'] or group['weekday']:
                    if verbose:
                        print('relative_day or weekday')
                    start = Date(res.string, offset=offset, tz=tz, context=context)
                    end = start + '1 day'

                elif group.get('month_1'):
                    if verbose:
                        print('month_1')
                    start = Date(res.string, offset=offset, tz=tz, context=context)
                    start = start.replace(hour=0, minute=0, second=0)
                    end = start + '1 month'

                elif group['date_5'] or group['date_6']:
                    if verbose:
                        print('date_5 or date_6')
                    start = Date(res.string, offset=offset, tz=tz)
                    year = g('year', 'year_2', 'year_3', 'year_4', 'year_5', 'year_6')
                    month = g('month', 'month_2', 'month_3', 'month_4', 'month_5')
                    day = g('date', 'date_2', 'date_3', 'date_4')

                    if day:
                        end = start + '1 day'
                    elif month:
                        end = start + '1 month'
                    elif year is not None:
                        end = start + '1 year'
                    else:
                        end = start

                if not isinstance(start, Date):
                    start = Date(now)

                if group['time_2']:
                    if verbose:
                        print('time_2')
                    temp = Date(res.string, offset=offset, now=start, tz=tz).date
                    start = start.replace(hour=temp.hour,
                                          minute=temp.minute,
                                          second=temp.second)

                    hour = g('hour', 'hour_2', 'hour_3')
                    minute = g('minute', 'minute_2')
                    second = g('seconds')

                    if second:
                        end = start + '1 second'
                    elif minute:
                        end = start + '1 minute'
                    elif hour:
                        end = start + '1 hour'
                    else:
                        end = start

                if group['since']:
                    end = now
                elif group['until'] or group['by']:
                    end = start
                    start = now

                if start <= now <= end:
                    if context == Context.PAST:
                        end = now
                    elif context == Context.FUTURE:
                        start = now

            else:
                raise TimestringInvalid('Invalid range: %s' % start)

            if end is None:
                # no end provided, so assume 24 hours
                if isinstance(start, str):
                    start = Date(start)
                end = start + '24 hours'

            if start > end:
                start, end = copy(end), copy(start)

            if pgoffset:
                start = start - pgoffset
                if end != 'infinity':
                    end = end - pgoffset

            self._dates = (start, end)

        if self._dates[0] > self._dates[1]:
            self._dates = (self._dates[0], self._dates[1] + '1 day')

    def __repr__(self):
        return "<timestring.Range %s %s>" % (str(self), id(self))

    def __getitem__(self, index: int):
        return self._dates[index]

    def __str__(self):
        return self.format()

    def __nonzero__(self):
        # Ranges are natuarally always true in statments link: if Range
        return True

    def format(self, format_string='%x %X'):
        return "From %s to %s" % (self[0].format(format_string) if isinstance(self[0], Date) else str(self[0]),
                                  self[1].format(format_string) if isinstance(self[1], Date) else str(self[1]))

    @property
    def start(self):
        return self[0]

    @property
    def end(self):
        return self[1]

    @property
    def elapse(self, short=False, format=True, min=None, round=None):
        if self.start == 'infinity' or self.end == 'infinity':
            return "infinity"
        # years, months, days, hours, minutes, seconds
        full = [0, 0, 0, 0, 0, 0]
        elapse = self[1].date - self[0].date
        days = elapse.days
        if days > 365:
            years = days / 365
            full[0] = years
            days = elapse.days - (years*365)
        if days > 30:
            months = days / 30
            full[1] = months
            days = days - (days / 30)

        full[2] = days

        full[3], full[4], full[5] = tuple(map(int, map(float, str(elapse).split(', ')[-1].split(':'))))

        if round:
            r = ['years', 'months', 'days', 'hours', 'minutes', 'seconds']
            assert round in r[:-1], "round value is not allowed. Must be in "+",".join(r)
            if full[r.index(round)+1] > dict(months=6, days=15, hours=12, minutes=30, seconds=30).get(r[r.index(round)+1]):
                full[r.index(round)] += 1

            min = r[r.index(round)+1]

        if min:
            m = ['years', 'months', 'days', 'hours', 'minutes', 'seconds']
            assert min in m, "min value is not allowed. Must be in "+",".join(m)
            for x in range(6-m.index(min)):
                full[5-x] = 0

        if format:
            if short:
                return re.sub('((?<!\d)0\w\s?)', '', "%dy %dm %dd %dh %dm %ss" % tuple(full))
            else:
                return re.sub('((?<!\d)0\s\w+\s?)', '', "%d years %d months %d days %d hours %d minutes %d seconds" % tuple(full))
        return full

    @property
    def tz(self):
        if self.start != 'infinity':
            return self.start.tz
        if self.end != 'infinity':
            return self.end.tz

    @tz.setter
    def tz(self, tz: datetime.tzinfo):
        self.start.tz = tz
        self.end.tz = tz

    def __len__(self):
        """Returns how many `seconds` the `Range` lasts.
        """
        return abs(int(self[1].to_unixtime() - self[0].to_unixtime()))

    def __lt__(self, other):
        return self.cmp(other) == -1

    def __gt__(self, other):
        return self.cmp(other) == 1

    def __eq__(self, other):
        return self.cmp(other) == 0

    def cmp(self, other):
        """*Note: checks Range.start() only*
        Key: self = [], other = {}
            * [   {----]----} => -1
            * {---[---}  ] => 1
            * [---]  {---} => -1
            * [---] same as {---} => 0
            * [--{-}--] => -1
        """
        if isinstance(other, Range):
            # other has tz, I dont, so replace the tz
            start = self.start.replace(tzinfo=other.start.tz) if other.start.tz and self.start.tz is None else self.start
            end = self.end.replace(tzinfo=other.end.tz) if other.end.tz and self.end.tz is None else self.end

            if start == other.start and end == other.end:
                return 0
            elif start < other.start:
                return -1
            else:
                return 1

        elif isinstance(other, Date):
            if other.tz and self.start.tz is None:
                return 0 if other == self.start.replace(tzinfo=other.tz) else -1 if other > self.start.replace(tzinfo=other.start.tz) else 1
            return 0 if other == self.start else -1 if other > self.start else 1
        else:
            return self.cmp(Range(other, tz=self.start.tz))

    def __contains__(self, other):
        """*Note: checks Range.start() only*
        Key: self = [], other = {}
            * [---{-}---] => True else False
        """
        if isinstance(other, Date):

            # ~ .... |
            if self.start == 'infinity' and self.end >= other:
                return True

            # | .... ~
            elif self.end == 'infinity' and self.start <= other:
                return True

            elif other == 'infinity':
                # infinitys cannot be contained, unless I'm infinity
                return self.start == 'infinity' or self.end == 'infinity'

            elif other.tz and self.start.tz is None:
                # we can safely update tzinfo
                return self.start.replace(tzinfo=other.tz).to_unixtime() <= other.to_unixtime() <= self.end.replace(tzinfo=other.tz).to_unixtime()

            return self.start <= other <= self.end

        elif isinstance(other, Range):
            # ~ .... |
            if self.start == 'infinity':
                # ~ <-- |
                return other.end <= self.end

            # | .... ~
            elif self.end == 'infinity':
                # | --> ~
                return self.start <= other.start

            elif other.start.tz and self.start.tz is None:
                return self.start.replace(tzinfo=other.start.tz).to_unixtime() <= other.start.to_unixtime() <= self.end.replace(tzinfo=other.start.tz).to_unixtime() \
                       and self.start.replace(tzinfo=other.start.tz).to_unixtime() <= other.end.to_unixtime() <= self.end.replace(tzinfo=other.start.tz).to_unixtime()

            return self.start <= other.start <= self.end and self.start <= other.end <= self.end

        else:
            return self.__contains__(Range(other, tz=self.start.tz))

    def plus_(self, num, unit: str, sign: int = 1):
        return Range(self.start.plus_(num, unit, sign),
                     self.end.plus_(num, unit, sign))

    def plus(self, duration: Union[str, int, float]):
        """ :return: a new instance, like datetime does"""
        return Range(self.start.plus(duration),
                     self.end.plus(duration),
                     tz=self.start.tz)
    def prev(self, times=1):
        """:return: a new instance of self times is not supported yet."""
        return Range(self.start - self.elapse,
                     copy(self.start), tz=self.start.tz)

    def next(self, times=1):
        """:return: a new instance of self times is not supported yet."""
        return Range(copy(self.end),
                     self.end + self.elapse, tz=self.start.tz)

    def __add__(self, duration: Union[str, int, float]):
        return self.plus(duration)

    def __sub__(self, duration: Union[str, int, float]):
        if type(duration) in (str, unicode):
            if duration.startswith('-'):
                duration = duration[1:]
            else:
                duration = '-' + duration
        elif type(duration) in (int, long, float):
            duration *= -1
        return self.plus(duration)

    def cut(self, by: Union[str, int, float], from_start=False):
        """:return: A copy of this Range shortened by the given duration"""
        s, e = self
        if from_start:
            s += by
        else:
            e -= by
        return Range(s, e)
