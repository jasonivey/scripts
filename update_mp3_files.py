import os
import sys
import eyed3

af = eyed3.load('01 - Matt Haig - The Humans.mp3')
af.tag.album = u'The Humans'
af.tag.title = u'The Humans'
af.tag.track_num = 1
af.tag.album_artist = u'Matt Haig'
af.tag.artist = u'Matt Haig'
af.tag.recording_date = 1996
af.tag.save()

