from builtins import str
from past.builtins import basestring
import decimal
import re
import time

def decimal2implicit(value, implicit):
    """ convert a decimal value into a string with an implicit decimal point.

    decimal2implicit(Decimal("234.45"), 2) -> "23445"
    decimal2implicit(Decimal("8.6"), 3) -> "8600"
    decimal2implicit(Decimal("4.5"), 0) -> "4"

    It took working out a partial implementation to realize this simple
    solution.
    """
    return (value * (10 ** implicit)).to_integral()


def parse_decimal(s, p1=re.compile("^(\.\d+)$"),
                     p2=re.compile("^.*?(\d+\.\d+).*$"),
                     p3=re.compile("^.*?(\d+).*$")):
    """ Strips out a real number from an arbitrary string. If no number can
    be found, returns None. Useful for currency parsing.
    """
    if not isinstance(s, basestring):
        return decimal.Decimal(s)
    s = s.replace(",", "")

    for p in [p1, p2, p3]:
        match = p.match(s)
        if match:
            return decimal.Decimal(match.groups()[0])
    try:
        return decimal.Decimal(s)
    except decimal.InvalidOperation:
        return None


def _findall(text, substr):
     # Also finds overlaps
     sites = []
     i = 0
     while 1:
         j = text.find(substr, i)
         if j == -1:
             break
         sites.append(j)
         i=j+1
     return sites

# I hope I did this math right. Every 28 years the
# calendar repeats, except through century leap years
# excepting the 400 year leap years. But only if
# you're using the Gregorian calendar.

def strftime(dt, fmt):
     if dt.year > 1900:
         return time.strftime(fmt, dt.timetuple())

     # WARNING: known bug with "%s", which is the number
     # of seconds since the epoch. This is too harsh
     # of a check. It should allow "%%s".
     fmt = fmt.replace("%s", "s")

     year = dt.year
     # For every non-leap year century, advance by
     # 6 years to get into the 28-year repeat cycle
     delta = 2000 - year
     off = 6*(delta // 100 + delta // 400)
     year = year + off

     # Move to around the year 2000
     year = year + ((2000 - year)//28)*28
     timetuple = dt.timetuple()
     s1 = time.strftime(fmt, (year,) + timetuple[1:])
     sites1 = _findall(s1, str(year))

     s2 = time.strftime(fmt, (year+28,) + timetuple[1:])
     sites2 = _findall(s2, str(year+28))

     sites = []
     for site in sites1:
         if site in sites2:
             sites.append(site)

     s = s1
     syear = "%4d" % (dt.year,)
     for site in sites:
         s = s[:site] + syear + s[site+4:]
     return s
