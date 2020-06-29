#!/usr/bin/env python3
# vim: awa:sts=4:ts=4:sw=4:et:cin:fdm=manual:tw=120:ft=python
# autowriteall, softtabstop, tabstop, shiftwidth, expandtab, cindent, foldmethod, textwidth, filetype

from ansimarkup import AnsiMarkup, parse
import argparse
import os
import pathlib
import regex
import sqlite3
import sys
import traceback

user_tags = {
    'info'        : parse('<bold><green>'),    # bold green
    'lowinfo'     : parse('<green>'),          # green
    'error'       : parse('<bold><red>'),      # bold red
    'warn'        : parse('<bold><yellow>'),   # bold yellow
}

am = AnsiMarkup(tags=user_tags)

_VERBOSE = 0
_SQL_SCHEMA = '''
    CREATE TABLE IF NOT EXISTS fortunes (
        id INTEGER PRIMARY KEY,
        quote TEXT,
        author TEXT,
        subject_id INTEGER
    );

    CREATE INDEX IF NOT EXISTS idx_fortune_subject_id ON fortunes (subject_id);

    CREATE TABLE IF NOT EXISTS subject(
        id INTEGER PRIMARY KEY,
        name TEXT
    );

    CREATE UNIQUE INDEX IF NOT EXISTS idx_subject_id ON subject (id, name);
'''

def _verbose_print(msg):
    if _VERBOSE > 0:
        am.ansiprint(f'<info>INFO: {msg}</info>', file=sys.stdout)

def _low_info_print(msg):
    if _VERBOSE > 1:
        am.ansiprint(f'<lowinfo>INFO: {msg}</lowinfo>', file=sys.stdout)

def _warning_print(msg):
    am.ansiprint(f'<warn>WARNING: {msg}</warn>', file=sys.stderr)

def _error_print(msg):
    am.ansiprint(f'<error>ERROR: {msg}</error>', file=sys.stderr)

def _parse_args():
    parser = argparse.ArgumentParser(description='Transform fortune text file into a structured text database file')
    parser.add_argument('input', metavar='INPUT', nargs='*', help='specify which fortune text files to parse')
    parser.add_argument('-d', '--database', default='fortune.db', help='specify where and what to name the output database')
    parser.add_argument('-r', '--restore', action="store_true", help='restore data from <database> to <INPUT>.txt')
    parser.add_argument('--verbose', '-v', action='count', default=0, help='increase output verbosity')
    args = parser.parse_args()
    global _VERBOSE
    _VERBOSE = args.verbose
    restore = args.restore
    database_path = pathlib.Path(args.database).resolve()
    input_paths = []
    if len(args.input) > 0:
        for filename in args.input:
            path = pathlib.Path(filename)
            if not path.is_file() and not restore:
                parser.error(f'{path} must exist to be inported into database')
            elif path.is_file() and restore:
                _warning_print(f'{path} is going to be overwritten with contents of database')
                input_paths.append(path.resolve())
            else:
                input_paths.append(path.resolve())
    return restore, input_paths, database_path

class dbopen(object):
    # Simple context manager for sqlite3 databases. Commits everything at exit.
    def __init__(self, path):
        self._path = path

    def __enter__(self):
        self.connection = sqlite3.connect(str(self._path))
        self.cursor = self.connection.cursor()
        self.cursor.row_factory = sqlite3.Row
        return self.cursor

    def __exit__(self, exc_class, exc, traceback):
        self.connection.commit()
        self.connection.close()

class Quote(object):
    def __init__(self, body=None, quote=None):
        self._body = body.splitlines() if body else []
        self._author = quote.splitlines() if quote else []

    def add_body(self, body_part):
        self._body.append(body_part)

    def add_author(self, author_part):
        self._author.append(author_part)

    @property
    def body(self):
        return '\n'.join(self._body)

    @property
    def author(self):
        return '\n'.join(self._author)

    def __str__(self):
        s = ''
        if self.body:
            s += self.body
        if self.author:
            first = True
            for author_part in self._author:
                s += f'\n        ― {author_part}' if first else f'\n           {author_part}'
                first = False
        return s

FORTUNE_SPLIT_PATTERN = r'^%$'
FORTUNE_SPLIT_REGEX = regex.compile(FORTUNE_SPLIT_PATTERN, regex.MULTILINE)
FORTUNE_AUTHOR_PATTERN = r'^\s+\p{Pd}+\s*(?P<author>.*)$'
FORTUNE_AUTHOR_REGEX = regex.compile(FORTUNE_AUTHOR_PATTERN)

def _parse_fortunes(data):
    for fortune in FORTUNE_SPLIT_REGEX.split(data):
        quote = Quote()
        for line in fortune.splitlines():
            if quote.author:
                quote.add_author(line.strip())
                continue
            author_match = FORTUNE_AUTHOR_REGEX.search(line)
            if author_match:
                author = author_match.group('author').strip()
                quote.add_author(author)
            else:
                quote.add_body(line.strip())
        _low_info_print(f'yielding quote: {quote}')
        yield quote

def _generate_fortunes(data, subject_id):
    for fortune in _parse_fortunes(data):
        if fortune.author:
            yield (fortune.body, fortune.author, subject_id)
        else:
            yield (fortune.body, '', subject_id)

def _clean_fortune_db(cursor, subject):
    _verbose_print(f'clearing database of existing {subject} quotes')
    cursor.execute('SELECT id FROM subject WHERE name=(:name)', {'name': subject})
    row = cursor.fetchone()
    subject_id = row['id'] if row else None
    if subject_id is None:
        _verbose_print(f'no {subject} quotes were found existing in the databse')
        return
    cursor.execute('DELETE FROM fortunes WHERE subject_id=?', (subject_id,))
    cursor.execute('DELETE FROM subject WHERE id=?', (subject_id,))

def _convert_fortune(path, cursor):
    _clean_fortune_db(cursor, path.stem)
    data = path.read_text()
    _verbose_print(f'total quotes in {path}: {data.count("%")}')
    cursor.execute('INSERT INTO subject (name) VALUES (:name)', {'name': path.stem})
    fortune_id = cursor.lastrowid
    cursor.executemany('INSERT INTO fortunes (quote, author, subject_id) VALUES (?, ?, ?)', _generate_fortunes(data, fortune_id))

def convert_fortunes(paths, database_path):
    with dbopen(database_path) as cursor:
        cursor.executescript(_SQL_SCHEMA)
        for path in paths:
            _convert_fortune(path, cursor)

def _restore_fortune(path, cursor):
    cursor.execute('SELECT id FROM subject WHERE name=(:name)', {'name': path.stem})
    row = cursor.fetchone()
    subject_id = row['id'] if row else None
    if subject_id is None:
        _error_print(f'finding {path.stem} as a valid fortune subject')
        return

    _verbose_print(f'found subject {path.stem} as subject id: {subject_id}')
    with path.open('w') as file_path:
        first = True
        for row in cursor.execute('SELECT quote, author FROM fortunes WHERE subject_id=?', (subject_id,)):
            quote = Quote(row['quote'], row['author'])
            file_path.write(f'{quote}' if first else f'\n%{quote}')
            first = False

def restore_fortunes(paths, database_path):
    with dbopen(database_path) as cursor:
        cursor.executescript(_SQL_SCHEMA)
        for path in paths:
            _restore_fortune(path, cursor)

def main():
    restore, paths, database_path = _parse_args()
    retval = 0
    try:
        if restore:
            restore_fortunes(paths, database_path)
        else:
            convert_fortunes(paths, database_path)
    except:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stderr)
        retval = 1
    return retval

if __name__ == '__main__':
    sys.exit(main())
