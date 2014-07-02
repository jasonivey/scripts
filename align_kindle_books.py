#!/usr/bin/env python
import os
import sys
import re
import glob
from datetime import *

if __name__ == '__main__':
    data = None
    with open(r'd:\out.txt') as file:
        data = file.read()

    books = []
    for match in re.finditer(r'Title:\s*(?P<Title>[^\n]*)\n(Author|Creator):\s*(?P<Author>[^\n]*)\nDate Acquired:\s*(?P<DateAcquired>[^\n]+)\n', data, re.S):
        title = match.group('Title').strip()
        author = match.group('Author').strip()
        date_acquired = datetime.strptime(match.group('DateAcquired').strip(), '%B %d, %Y')
        books.append([title, author, date_acquired])
        
    total_titles = len(re.findall('Title:', data))
    total_books = len(books)
    total_missing = 0
    
    if total_titles != total_books:
        index = 0
        for match in re.finditer(r'Title:', data):
            title = books[index][0]
            line = data[match.start() : data.find('\n', match.start())].strip()
            if line.find(title) == -1:
                print('ERROR: The following title wasn\'t picked up by the search:\n\t%s' % line)
                total_missing += 1
            else:
                index += 1

    #print('total_titles: %s' % total_titles)
    #print('total_books: %s' % total_books)
    assert( total_titles == total_books + total_missing )
    
    with open(r'd:\out1.txt', 'w') as output:
        books.sort(lambda x, y: cmp(x[0].lower(), y[0].lower()))
        output.write('%d Books sorted by Title\n\n' % len(books))
        for book in books:
            output.write('%s %s %s\n' % (book[0], book[1], book[2].strftime('%B %d, %Y')))
        books.sort(lambda x, y: cmp(x[2], y[2]))
        output.write('\n\n\n%d Books sorted by Date Acquired\n\n' % len(books))
        for book in books:
            output.write('%s %s %s\n' % (book[0], book[1], book[2].strftime('%B %d, %Y')))
            
    entries = glob.glob('k:/books/*.epub')
    
    for book in books:
        title = book[0]
        index = -1
        for i, entry in enumerate(entries):
            if entry.lower().find(title.lower()) != -1:
                index = i
                break;

        if index == -1:
            print('Unable to find %s' % title)
    
    