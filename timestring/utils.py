from word2number import w2n

from timestring import TimestringInvalid


def get_num(num):
    """
    :param num: int, float or string repersenting a number, such as '1.5' or
    'one'
    """
    if isinstance(num, (int, float)):
        return num

    if 'couple' in (num or ''):
        return 2

    try:
        return int(num)
    except ValueError:
        try:
            return float(num)
        except ValueError:
            try:
                return w2n.word_to_num(num or 'one')
            except ValueError:
                raise TimestringInvalid('Unknown number: %s' % num)
