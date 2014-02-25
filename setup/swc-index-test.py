#!/usr/bin/env python

'''Test script to check whether index.html is valid.

Execute this code at the command line by typing:

  python swc-index-test.py

Or

  python swc-index-test.py path/to/index.html

How to get a command line:

- On OSX run this with the Terminal application.

- On Windows, go to the Start menu, select 'Run' and type 'cmd'
(without the quotes) to run the 'cmd.exe' Windows Command Prompt.

- On Linux, either use your login shell directly, or run one of a
  number of graphical terminals (e.g. 'xterm', 'gnome-terminal', ...).

For some screen shots, see:

  http://software-carpentry.org/v5/setup.html

Run the script and follow the instructions it prints at the end.  If
you see an error saying that the 'python' command was not found, than
you may not have any version of Python installed.  See:

  http://www.python.org/download/releases/2.7.6/#download

for installation instructions.

Prints out warnings and errors when the header in index.html is malformed.

Checks for:
    1. There should be exactly 13 categories
    2. Categories are allowed to appear only once
    3. Contact email should be valid (letters + @ + letters + . + letters)
    4. Latitute/longitude should be 2 floating point numbers
    5. startdate/enddate should be valid dates
    6. country should be a string with no spaces
    7. instructor list should be a valid Python/Ruby list
    8. Template header should be removed
'''

import sys
import re

__version__ = '0.2'

# Currently, a header has exactly 13 elements
CATEGORIES = set(['layout', 'root', 'venue', 'address', 'country', \
        'humandate', 'humantime', 'startdate', 'enddate', 'latlng', \
        'registration', 'instructor', 'contact'])

def check_email(email):
    '''A valid email has letters, then an @, followed by letters, followed by a dot, followed by letters.'''
    if not re.match(r'[^@]+@[^@]+\.[^@]+', email):
        return False
    return True

def check_country(country):
    '''A valid country has no spaces, is one string'''
    if ' ' in country:
        return False
    return True

def check_latitude_longitude(latlng):
    '''A valid latitude/longitude listing is two floats, separated by comma'''
    try:
        lat, lng = latlng.split(',')
    except ValueError:
        # there are more or less than 2 values listed here
        return False
    try:
        # just one of them has to break
        float(lat)
        float(lng)
    except:
        return False
    return True

def check_date(date):
    '''A valid date is YEAR-MONTH-DAY, example: 2014-06-30'''
    from datetime import datetime
    try:
        datetime.strptime(date, '%Y-%m-%d')
    except ValueError:
        return False
    return True

def check_instructor(instructor):
    '''Checks whether instructor list is of format ['First name', 'Second name', ...']'''
    try:
        import ast # from Python 2.6 on
        ast.literal_eval(instructor)
        # Human names are complicated so I'll just leave it at that.
    except ImportError:
        # skip
        sys.stderr.write('WARN: module "ast" not found. Skipping test for instructor names.\n')
        return True
    except:
        # There was a problem with parsing the instructor list
        return False
    return True

def check_validity(data, function, error):
    '''Wrapper-function around the various check-functions.'''
    valid = function(data)
    if not valid:
        sys.stderr.write(error)
        sys.stderr.write('\tOffending entry was: "%s"\n' %(data))
        return True
    return False

def get_header(index_fh):
    '''Parses index.html file, returns just the header'''
    inside = False
    header = []
    for line in index_fh:
        line = line.rstrip('\n\r')
        if line == '---' and not inside:
            inside = True
            continue
        elif line == '---' and inside:
            inside = False

        if inside:
            header.append(line)
        if "This page is a template for bootcamp home pages." in line:
            sys.stderr.write('WARN:\tYou seem to still have the template header in your index.html. Please remove that.\n')
            sys.stderr.write('\tLook for: "<!-- Remove the block below. -->" in the index.html.\n')
            break # we can stop here - for now, just check header and template header
    return header

if __name__ == '__main__':
    args = sys.argv
    if len(args) > 2:
        sys.stderr.write('Usage: python swc-index-test.py\nAlternative: python swc-index-test.py path/to/index.html\n')
        sys.exit(0)
    elif len(args) == 1:
        filename = '../index.html'
    else:
        filename = args[1]

    sys.stderr.write('Testing file "%s".\n' %filename)
    index_fh = open(filename)

    header = get_header(index_fh)

    if not header:
        sys.stderr.write('ERROR:\tCan\'t find header in given file "%s". Please check path, is this the bc index.html?\n' %(filename))
        sys.exit(1)

    broken = False
    # to check whether all categories are present
    this_categories = []
    # look through all header entries
    for element in header:
        element_list = element.split(':')
        # This also splits human times, account for that
        if len(element_list) > 2:
            category, data = element_list[0], element_list[1:]
        else:
            category, data = element_list[0], element_list[1].strip()

        this_categories.append(category)

        if category == 'contact':
            broken |= check_validity(data, check_email, \
                    'ERROR:\tEmail seems to be invalid.\n')
        elif category == 'country':
            broken |= check_validity(data, check_country, \
                    'ERROR:\tCountry seems to be invalid. Check whether there are spaces inside the string.\n')
        elif category == 'latlng':
            broken |= check_validity(data, check_latitude_longitude, \
                    'ERROR:\tLatitude/Longitude seems to be invalid. Check whether it\'s two floating point numbers, separated by a comma.\n')
        elif (category == 'startdate') or (category == 'enddate'):
            broken |= check_validity(data, check_date, \
                    'ERROR:\t%s seems to be invalid. Must be of format year-month-day, i.e., 2014-01-31.\n' %category)
        elif category == 'instructor':
            broken |= check_validity(data, check_instructor, \
                    'ERROR:\tInstructor string isn\'t a valid list of format ["First instructor", "Second instructor",..].\n')

    # Double categories?
    if len(this_categories) != len(set(this_categories)):
        sys.stderr.write('ERROR:\tIdentical categories appear twice or more.\n')
        # this is a slightly ugly solution - collections.Counter might be nicer
        seen_set = set()
        for cat in this_categories:
            if cat in seen_set:
                sys.stderr.write('\t"%s" appears more than once.\n' %(cat))
            else:
                seen_set.add(cat)
        broken = True

    # See how many categories we got
    this_categories = set(this_categories)

    missing_categories = CATEGORIES - this_categories
    if missing_categories:
        sys.stderr.write('ERROR:\tnot enough categories.\n')
        sys.stderr.write('\tMissing: %s\n' %(list(missing_categories)))
        broken = True

    extra_categories = this_categories - CATEGORIES
    if extra_categories:
        sys.stderr.write('ERROR:\tThere are superfluous categories.\n')
        sys.stderr.write('\tToo many: %s\n' %(list(extra_categories)))
        broken = True

    if not broken:
        sys.stderr.write('Everything seems to be in order.\n')
        sys.exit(0)
    else:
        sys.stderr.write('There were problems, please see above.\n')
        sys.exit(1)
