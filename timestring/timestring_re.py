import re

MONTH_NAMES = r'''\b(january|february|march|april|june|july|august|september|october|november|december''' \
              r'''|jan|feb|mar|apr|may|jun|jul|aug|sept?|oct|nov|dec)\b'''

TIMESTRING_RE = re.compile(re.sub('[\t\n\s]', '', re.sub('(\(\?\#[^\)]+\))', '', r'''
    (
        ((?P<prefix>between|from|before|after|\>=?|\<=?|greater\s+th(a|e)n(\s+a)?|less\s+th(a|e)n(\s+a)?)\s+)?
        (
            (?P<unixtime>\d{10})
            |
            (
                (\b((?P<since>since)|(?P<until>until|till)|(?P<by>by))\s+)?
                (
                    (\b(?P<article>the\s)\s+)?
                    \b(?P<relative_day>day\s+before\s+yesterday|day\s+after\s+tomorrow|today|now|yesterday|tomorrow)\b
                    |
                    (\b
                        (?P<recurrence>
                            (?P<this>this|current)
                            |(?P<prev>last|prev(ious)|past|prior)
                            |(?P<next>next|upcoming|following)
                        )
                    \s+)?
                    (
                        (?# =-=-=-= Matches Days =-=-=-= )
                        (?P<weekday>\b(mondays?|tuesdays?|wednesdays?|thursdays?|fridays?|saturdays?|sundays?|mon|tues?|wedn?|thur?|fri|sat|sun)\b)
                        |
                        (?# =-=-=-= Matches:: number-frame-ago?, "4 weeks", "sixty days ago" =-=-=-= )
                        (?P<duration>
                            (\b(?P<in>in\s+))?
                            (?P<num>((\d+(\.\d+)?|couple(\s+of)?|one|two|twenty|twelve|three|thirty|thirteen|four(teen|ty)?|five|fif(teen|ty)|six(teen|ty)?|seven(teen|ty)?|eight(een|y)?|nine(teen|ty)?|ten|eleven|hundred)\s*)*)
                            (
                                \b(?P<delta>seconds?|minutes?|hours?|days?|weekends?|weeks?|months?|quarters?|years?)
                                |((?<![a-zA-Z])(?P<delta_2>[YyQqDdHhMmSs])(?!\w))
                            )
                        )
                        (\s+((?P<ago>ago)|(?P<from_now>from\s+now))\b)?
                        |
                        (?# =-=-=-= Matches dates with month name =-=-=-= )
                        (?P<date_5>
                            ((?P<year_6>(([12][089]\d{2})|('\d{2})))?([\/\-\s]+)?)
                            (
                                ((?P<date_4>(\d{1,2})(?!\d))(th|nd|st|rd)?([\/\-\s]+)?)
                                (\s+of\s+)?
                                (?P<month_5>''' + MONTH_NAMES + r''')[\/\-\s]?
                            )
                            |
                            (
                                (?P<month>''' + MONTH_NAMES + r''')[\/\-\s]?
                                ((?P<date>(\d{1,2})(?!\d))(th|nd|st|rd)?)
                            )
                            (,?\s(?P<year>([12][089]|')?\d{2}))?
                        )

                        |

                        (?# =-=-=-= Matches "2012/12/11", "2013-09-10T", "5/23/2012", "05/2012", "2012" =-=-=-= )
                        (?P<date_6>
                            ((?P<year_3>[12][089]\d{2})[/-](?P<month_3>[01]?\d)([/-](?P<date_3>[0-3]?\d))?)T?
                                |
                            ((?P<month_2>[01]?\d)[/-](?P<date_2>[0-3]?\d)[/-](?P<year_2>(([12][089]\d{2})|(\d{2}))))
                                |
                            ((?P<month_4>[01]?\d)[/-](?P<year_4>([12][089]\d{2})|(\d{2})))
                                |
                            (?P<year_5>([12][089]\d{2})|('\d{2}))
                        )

                        |

                        (?# =-=-=-= Matches "01:20", "6:35 pm", "7am", "noon" =-=-=-= )
                        (?P<time_2>
                            ((?P<hour>[012]?[0-9]):(?P<minute>[0-5]\d)\s*(?P<am>am|pm|p|a))
                                |
                            ((?P<hour_2>[012]?[0-9]):(?P<minute_2>[0-5]\d)(:(?P<seconds>[0-5]\d))?)\s*(?P<am_2>am|pm|p|a)?
                                |
                            ((?P<hour_3>[012]?[0-9])\s*((?P<am_1>am|pm|p|a)|o'?clock))
                                |
                            (?P<daytime>(after)?noon|morning|((around|about|near|by)\s+)?this\s+time|evening|(mid)?night(time)?)
                        )

                        |

                        (?P<month_1>''' + MONTH_NAMES + ''')
                    )
                )
                (?# =-=-=-= Conjunctions =-=-=-= )
                ,?(\s+(on|at|of|by|and|to|@))?\s*
            )+
        )
    )
    ''')), re.I)
