#!/usr/bin/env python
from __future__ import print_function
import argparse
import os
import re
import string
import sys


BOOK_TYPE_PDF = 'pdf'
BOOK_TYPE_CHM = 'chm'
BOOK_TYPE_EPUB = 'epub'

class Books:
    def __init__(self):
        self.books = []

    def import_from_dir_list(self, paths):
        for filename in paths:
            book = Book.create_from_filename(filename)
            self.books.append(book)
        self.books.sort()

    def read_from_catalog(self, file):
        for text in file.readlines():
            book = Book.create_from_catalog(text)
            self.books.append(book)
        self.books.sort()

    def write_to_catalog(self, file):
        for book in self.books:
            book.write_to_catalog(file)

    def __str__(self):
        books_str = []
        for book in self.books:
            books_str.append(str(book))
        return '\n'.join(books_str)

    def __eq__(self, other):
        if len(self.books) != len(self.books):
            return False
        self.books.sort()
        other.books.sort()
        for zipped_books in zip(self.books, other.books):
            if zipped_books[0] != zipped_books[1]:
                return False
        return True


class BookType:
    def __init__(self, text):
        if 'pdf' in text.lower():
            self.type = BOOK_TYPE_PDF
        elif 'chm' in text.lower():
            self.type = BOOK_TYPE_CHM
        elif 'epub' in text.lower():
            self.type = BOOK_TYPE_EPUB
        else:
            assert('Unknown file type')
    def __str__(self):
        return self.type
    def __cmp__(self, other):
        return cmp(self.type, other.type)
    def __eq__(self, other):
        return self.type == other.type
    def __ne__(self, other):
        return self.type != other.type


class Book:
    def __init__(self, type, title, year, authors):
        self.type = type
        self.title = title
        self.year = year
        self.authors = authors
    
    @staticmethod
    def _get_book_pattern():
        anything_but_open_paren = '[^(]+'
        anything_but_close_paren = '[^)]+'
        paren_enclosed_text = r'\({0}\)'.format(anything_but_close_paren)
        return r'^(?P<year>{0})\s+(?P<title>{1})\s+(?P<authors>{0})$'.format(paren_enclosed_text, anything_but_open_paren)

    @staticmethod
    def create_from_filename(filename):
        basename, extension = os.path.splitext(filename)
        basename = basename[len(os.path.dirname(filename)) + 1:]
        match = re.match(Book._get_book_pattern(), basename)
        assert match
        title = match.group('title').strip()
        if '-' in title:
            # Only file names like 'book-name.pdf' or 'book - name.pdf' are acceptable
            assert re.search(r'(?:\S-\S)|(?:\s-\s)', title)
            title = title.replace(' - ', ': ')
        year = match.group('year').strip('() ')
        assert year.isdigit(), 'The year is not just digits'
        year = int(year)
        authors = [author.strip() for author in match.group('authors').strip('() ').split(',')]
        return Book(BookType(extension), title, year, authors)

    @staticmethod
    def create_from_catalog(text):
        pattern = '^(?P<year>[^;]+);(?P<title>[^;]+);(?P<authors>[^;]+);(?P<type>.*)$'
        match = re.match(pattern, text)
        assert match
        type = BookType(match.group('type').strip())
        title = match.group('title').strip()
        year = match.group('year').strip()
        assert year.isdigit(), 'The year is not just digits'
        year = int(year)
        authors = [author.strip() for author in match.group('authors').strip().split(',')]
        return Book(type, title, year, authors)
    
    def write_to_catalog(self, file):
        assert(';' not in self.title and ';' not in ','.join(self.authors))
        print('{0};{1};{2};{3}\n'.format(self.year, self.title, ','.join(self.authors), self.type), end='', file=file)
    
    def __str__(self):
        return '{0}\n\t{1}\n\t{2}\n\t{3}'.format(self.title, ', '.join(self.authors), self.year, self.type)
    
    def __cmp__(self, other):
        retval = cmp(self.title.lower(), other.title.lower())
        if retval:
            return retval
        retval = cmp(self.year, other.year)
        if retval:
            return retval
        self_authors = ','.join(sorted(self.authors, key=string.lower))
        other_authors = ','.join(sorted(other.authors, key=string.lower))
        retval = cmp(self_authors.lower(), other_authors.lower())
        if retval:
            return retval
        return cmp(self.type, other.type)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __eq__(self, other):
        if self.year != other.year:
            return False
        if self.title.lower() != other.title.lower():
            return False
        self_authors = ','.join(sorted(self.authors, key=string.lower))
        other_authors = ','.join(sorted(other.authors, key=string.lower))
        if self_authors.lower() != other_authors.lower():
            return False
        return self.type == other.type

    
def directory_exists(dir):
    if not os.path.isdir(dir):
        msg = "{0} is not a valid directory".format(dir)
        raise argparse.ArgumentTypeError(msg)
    return os.path.normpath(os.path.abspath(dir))

def parse_command_line():
    parser = argparse.ArgumentParser(description='Parse book titles')
    parser.add_argument('-d', '--dir', required=False, default=os.getcwd(), type=directory_exists, help='The directory which contains the book files')
    args = parser.parse_args()
    return args.dir

def main():
    dir = parse_command_line()
    
    paths = []
    for root, dirs, files in os.walk(dir):
        for filename in files:
            if filename.endswith('.pdf') or filename.endswith('.chm') or filename.endswith('.epub'):
                paths.append(os.path.join(root, filename))
    paths.sort(key=lambda filename: os.path.basename(filename).lower())
    
    books1 = Books()
    books1.import_from_dir_list(paths)
    with open(os.path.join(dir, 'catalog.txt'), 'w') as catalog:
        books1.write_to_catalog(catalog)
    
    books2 = Books()
    with open(os.path.join(dir, 'catalog.txt')) as catalog:
        books2.read_from_catalog(catalog)
        
    assert books1 == books2
    #print(str(books))

if __name__ == '__main__':
    sys.exit(main())
    
