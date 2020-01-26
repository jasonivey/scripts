import os
import sys
import eyed3

af = eyed3.load('01 - Matt Haig - The Humans.mp3')
af.tag.album = 'The Humans'
af.tag.title = 'The Humans'
af.tag.track_num = 1
af.tag.album_artist = 'Matt Haig'
af.tag.artist = 'Matt Haig'
af.tag.recording_date = 1996
af.tag.save()

