import re
import pytz
from copy import copy
from datetime import datetime, timedelta

from timestring.Date import Date
from timestring import TimestringInvalid
from timestring.timestring_re import TIMESTRING_RE
from timestring.utils import get_timezone_time

try:
    unicode
except NameError:
    unicode = str
    long = int

CONTEXT_PAST = -1
CONTEXT_FUTURE = 1


class Range(object):
    def __init__(self, start, end=None, offset=None, start_of_week=0, tz=None,
                 verbose=False, context=None):
        """`start` can be type <class timestring.Date> or <type str>
        """
        self._dates = []
        pgoffset = None
        if tz:
            tz = pytz.timezone(str(tz))

        if start is None:
            raise TimestringInvalid("Range object requires a start valie")

        if not isinstance(start, (Date, datetime)):
            start = str(start)
        if end and not isinstance(end, (Date, datetime)):
            end = str(end)

        if start and end:
            self._dates = (Date(start, tz=tz), Date(end, tz=tz))

        elif start == 'infinity':
            self._dates = (Date('infinity'), Date('infinity'))

        elif isinstance(start, (int, long, float)) \
                    or (isinstance(start, (str, unicode)) and start.isdigit()) \
                and len(str(int(float(start)))) > 4:
            start = Date(start)
            end = start + '1 second'
            self._dates = start, end

        elif re.search(r'(\s(and|to)\s)', start):
            # Both sides are provided in string "start"
            start = re.sub('^(between|from)\s', '', start.lower())
            # Both arguments found in start variable
            r = tuple(re.split(r'(\s(and|to)\s)', start.strip()))
            start = Range(r[0], tz=tz).start
            self._dates = (start, Range(r[-1], tz=tz).start)

        elif re.match(r"(\[|\()((\"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}(\.\d+)?(\+|\-)\d{2}\")|infinity),((\"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}(\.\d+)?(\+|\-)\d{2}\")|infinity)(\]|\))", start):
            # Postgresql tsrange and tstzranges support
            start, end = tuple(re.sub('[^\w\s\-\:\.\+\,]', '', start).split(','))
            self._dates = (Date(start), Date(end))

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

                if (group.get('delta') or group.get('delta_2')) is not None:
                    delta = (group.get('delta') or group.get('delta_2')).lower()

                    start = Date("now", offset=offset, tz=tz)
                    di = "%s %s" % (str(int(group['num'] or 1)), delta)

                    # "next 2 weeks", "the next hour"   x[     ][     ]
                    if group['ref'] in ['next'] and (group['num'] or group['article']):
                        if int(group['num'] or 1) > 1:
                            di = "%s %s" % (str(int(group['num'] or 1)), delta)
                        end = start + di

                    # "next week", "upcoming 3 weeks"   (  x  )[      ]
                    elif group['ref'] in ['next', 'upcoming']:
                        this = Range('this ' + delta, offset=offset, tz=tz)
                        start = this.end
                        end = start + di

                    # ago                               [     ](     )x
                    elif group['ago']:
                        start = Date(res.string)
                        if not re.match('(hour|minute|second)s?', delta):
                            start = start.replace(hour=0, minute=0, second=0)
                            end = start + '1 day'
                        elif delta.startswith('hour'):
                            start = start.replace(minute=0, second=0)
                            end = start + '1 hour'
                        elif delta.startswith('minute'):
                            start = start.replace(second=0)
                            end = start + '1 minute'
                        else:
                            end = start + '1 second'

                    # "last 2 weeks", "the last hour"   [     ][     ]x
                    elif group['ref'] in ['last'] and (group['num'] or group['article']):
                        end = start - di

                    # "last week", "previous 3 weeks"   [     ](  x  )
                    elif group['ref'] in ['last', 'previous', '']:
                        this = Range('this ' + delta, offset=offset, tz=tz)
                        start = this.start - di
                        end = this.end - di

                    # "1 year", "10 days" till now
                    elif group['num']:
                        end = start - group['main']

                    # this                             [   x  ]
                    elif group['ref'] in ['this', 'current', None]:

                        if delta.startswith('y'):
                            start = Date(datetime(now.year, 1, 1), offset=offset, tz=tz)

                        # month
                        elif delta.startswith('mo'):
                            start = Date(datetime(now.year, now.month, 1), offset=offset, tz=tz)

                        # week
                        elif delta.startswith('w'):
                            d = datetime(now.year, now.month, now.day)
                            start = Date(d - timedelta(days=d.weekday()), offset=offset)

                        # day
                        elif delta.startswith('d'):
                            start = Date("today", offset=offset, tz=tz)

                        # hour
                        elif delta.startswith('h'):
                            start = Date("today", offset=offset, tz=tz)

                        # minute
                        elif delta.startswith('m'):
                            start = Date('now', offset=offset, tz=tz)

                        # second
                        elif delta.startswith('s'):
                            start = Date("now", offset=offset, tz=tz)

                        else:
                            raise TimestringInvalid("Not a valid time reference")

                        end = start + di

                elif group['day_2']:
                    # Relative day: "today" etc
                    # Week day: "Monday" etc
                    start = Date(group['day_2'], offset=offset, tz=tz)
                    start = start.replace(hour=0, minute=0, second=0)
                    if group['ref'] in ['last', 'prev', 'previous']:
                        start -= '1 week'
                    elif group['ref'] in ['next', 'upcoming'] and start.weekday == now.isoweekday():
                        start += '1 week'
                    end = start + '1 day'

                elif group['day_3']:
                    # "Day after tomorrow", "Day after yesterday"
                    start = Date(group['day_3'], offset=offset, tz=tz)
                    start = start.replace(hour=0, minute=0, second=0)
                    end = start + '1 day'

                elif group.get('month_1'):
                    if group['year_5']:
                        start = Date(start, offset=offset, tz=tz)
                        start = start.replace(hour=0, minute=0, second=0)
                    else:
                        # A whole month of this, previous or next year
                        start = Date(group['month_1'], offset=offset, tz=tz)
                        start = start.replace(hour=0, minute=0, second=0)
                        if group['ref'] in ['last', 'prev', 'previous', 'past']:
                            start -= '1 year'
                        elif group['ref'] in ['next', 'upcoming'] and start.weekday == now.weekday:
                            start += '1 year'
                    end = start + '1 month'

                elif group['date_5'] or group['date_6']:
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
                    temp = Date(res.string, offset=offset, tz=tz).date
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

                if start <= now <= end:
                    if context == CONTEXT_PAST:
                        end = now
                    elif context == CONTEXT_FUTURE:
                        start = now
            else:
                raise TimestringInvalid("Invalid timestring request")


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

    def __getitem__(self, index):
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
    def tz(self, tz):
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

    def cut(self, by, from_start=True):
        """Shorten this range by the range requested and return the new range
        """
        s, e = copy(self.start), copy(self.end)
        if from_start:
            e = s + by
        else:
            s = e - by
        return Range(s, e)

    def adjust(self, to):
        # return a new instane, like datetime does
        return Range(self.start.adjust(to),
                     self.end.adjust(to), tz=self.start.tz)

    def next(self, times=1):
        """Returns a new instance of self
        times is not supported yet.
        """
        return Range(copy(self.end),
                     self.end + self.elapse, tz=self.start.tz)

    def prev(self, times=1):
        """Returns a new instance of self
        times is not supported yet.
        """
        return Range(self.start - self.elapse,
                     copy(self.start), tz=self.start.tz)

    def __add__(self, to):
        return self.adjust(to)

    def __sub__(self, to):
        if type(to) in (str, unicode):
            to = to[1:] if to.startswith('-') else ('-'+to)
        elif type(to) in (int, long, float):
            to = to * -1
        return self.adjust(to)
