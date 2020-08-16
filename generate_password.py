#!/usr/bin/env python3
# vim: awa:sts=4:ts=4:sw=4:et:cin:fdm=manual:tw=120:ft=python

from ansimarkup import ansiprint
from app_settings import app_settings
import argparse
import secrets
import string
import sys
import traceback

class PasswordGenerator:
    def __init__(self, length, min_lower_case_chars, min_upper_case_chars, min_numeric_chars, min_punctuation_chars, exclude_list):
        self._length = length
        self._min_lower_case_chars = min_lower_case_chars
        self._min_upper_case_chars = min_upper_case_chars
        self._min_numeric_chars  = min_numeric_chars
        self._min_punctuation_chars = min_punctuation_chars
        self._alphabet = string.ascii_lowercase + string.ascii_uppercase + string.digits + string.punctuation
        if len(exclude_list):
            self._alphabet = ''.join(set(self._alphabet) - set(exclude_list))

    def _is_valid(self, password):
        lower_count, upper_count, numeric_count, punctuation_count = 0, 0, 0, 0
        for c in password:
            if c.islower(): lower_count += 1
            elif c.isupper(): upper_count += 1
            elif c.isdigit(): numeric_count += 1
            elif c in string.punctuation: punctuation_count += 1
        return lower_count >= self._min_lower_case_chars and \
               upper_count >= self._min_upper_case_chars and \
               numeric_count >= self._min_numeric_chars and \
               punctuation_count >= self._min_punctuation_chars

    def generate(self):
        for i in range(1, 100):
            password = secrets.choice(string.ascii_lowercase + string.ascii_uppercase)
            password += ''.join(secrets.choice(self._alphabet) for i in range(self._length - 1))
            if self._is_valid(password):
                app_settings.info(f'returning the {i} generated password')
                return password

def _parse_args():
    parser = argparse.ArgumentParser(description=f'Generate random password from [{string.ascii_lowercase + string.ascii_uppercase + string.digits + string.punctuation}] characters')
    parser.add_argument('-v', '--verbose', action='count', default=0, help='increase output verbosity')
    parser.add_argument('-c', '--count', type=int, default=32, help='how many total characters should be in the password')
    parser.add_argument('-l', '--lower-case', type=int, default=1, help='how many lower case letters must be in the password')
    parser.add_argument('-u', '--upper-case', type=int, default=1, help='how many upper case letters must be in the password')
    parser.add_argument('-n', '--numbers', type=int, default=1, help='how many numbers must be in the password')
    parser.add_argument('-p', '--punctuation', type=int, default=1, help='how many punctuation characters must be in the password')
    parser.add_argument('-x', '--exclude', type=str, default='', help='any characters which should not be allowed')
    args = parser.parse_args()
    app_settings.update(vars(args))
    app_settings.print_settings(print_always=False)

def generate_password(length, min_lower_case_chars, min_upper_case_chars, min_numeric_chars, min_punctuation_chars, exclude):
    password_generator = PasswordGenerator(length, \
                                           min_lower_case_chars, \
                                           min_upper_case_chars, \
                                           min_numeric_chars, \
                                           min_punctuation_chars, \
                                           exclude)
    return password_generator.generate()

def main():
    _parse_args()
    try:
        password = generate_password(app_settings.count, app_settings.lower_case, \
                                     app_settings.upper_case, app_settings.numbers, \
                                     app_settings.punctuation, app_settings.exclude)
        ansiprint(f'<b,g,>Password: </b,g,><b,w,>{password}</b,w,>')
    except:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stderr)
        return 1
    return 0

if __name__ == '__main__':
    sys.exit(main())
