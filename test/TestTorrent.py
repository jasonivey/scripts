import os, sys, stat, unittest, mx.DateTime

sys.path.append( os.path.abspath('..') )
from Torrent import *

class TestTorrent(unittest.TestCase):
    def setUp(self):
        file = open('test.torrent', 'rb')
        self.mData = file.read()
        file.close()
        
    def testParse(self):
        torrent = Torrent(self.mData)
        self.assertEqual( torrent.mName, 'Audiobook - George Orwell - 1984' )
        self.assertEqual( torrent.mAuthor, '' )
        self.assertEqual( torrent.mComment, '' )
        self.assertEqual( torrent.mAnnounce, 'http://inferno.demonoid.com:3389/announce' )
        self.assertEqual( torrent.mAnnounceList, ['http://inferno.demonoid.com:3389/announce',
                                                  'http://tv.tracker.prq.to/announce',
                                                  'http://tracker.desitorrents.com:6969/announce',
                                                  'http://www.pcttracker.com:2710/announce'] )
        self.assertEqual( torrent.mCreationDate, mx.DateTime.DateTime(2006, 1, 8, 10, 22,3.0) )
        self.assertEqual( torrent.mFiles[0].mPath, 'George Orwell - 1984 01.mp3' )
        self.assertEqual( torrent.mFiles[1].mPath, 'George Orwell - 1984 02.mp3' )
        self.assertEqual( torrent.mFiles[2].mPath, 'George Orwell - 1984 03.mp3' )
        self.assertEqual( torrent.mFiles[3].mPath, 'George Orwell - 1984 04.mp3' )
        self.assertEqual( torrent.mFiles[4].mPath, 'George Orwell - 1984 05.mp3' )
        self.assertEqual( torrent.mFiles[5].mPath, 'George Orwell - 1984 06.mp3' )
        self.assertEqual( torrent.mFiles[6].mPath, 'George Orwell - 1984 07.mp3' )
        self.assertEqual( torrent.mFiles[7].mPath, 'George Orwell - 1984 08.mp3' )
        self.assertEqual( torrent.mFiles[8].mPath, 'George Orwell - 1984 09.mp3' )
        self.assertEqual( torrent.mFiles[9].mPath, 'George Orwell - 1984 10.mp3' )
        self.assertEqual( torrent.mFiles[10].mPath, 'George Orwell - 1984 11.mp3' )
        self.assertEqual( torrent.mFiles[11].mPath, 'George Orwell - 1984 12.mp3' )
        self.assertEqual( torrent.mFiles[12].mPath, 'George Orwell - 1984 13.mp3' )
        self.assertEqual( torrent.mFiles[13].mPath, 'George Orwell - 1984 14.mp3' )
        self.assertEqual( torrent.mFiles[14].mPath, 'George Orwell - 1984.jpg' )
        self.assertEqual( torrent.mFiles[15].mPath, 'Tracked_by_Demonoid_com.txt' )
        self.assertEqual( torrent.mSize, 240769898 )
        self.assertEqual( torrent.mPieceLength, 256 * 1024 )
        self.assertEqual( torrent.mPieceCount, 919 )
        self.assertEqual( len(torrent.mPieces), 20 * torrent.mPieceCount )
        self.assertEqual( torrent.mPrivate, False )
        self.assertEqual( torrent.mSHA1s[10], '7540b46ede85a75bb41a6f21ed16b77d7e293d' )
        self.assertEqual( torrent.mSHA1s[354], '5f1f9f8fc6be1962e01517b9fbcaf1d699963f3' )
        self.assertEqual( torrent.mSHA1s[589], 'bdcee2ae671c9b3aebca8cd4ba22bb701a3415cc' )
        self.assertEqual( torrent.mNodes[1], IpAddress('65.189.146.171:12242') )
        self.assertEqual( torrent.mNodes[4], IpAddress('61.31.187.22:17848') )
        self.assertEqual( torrent.mNodes[9], IpAddress('82.144.172.250:17485') )

if __name__ == '__main__':
    unittest.main()
