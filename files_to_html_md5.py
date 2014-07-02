import os
import sys
import hash_utils

def StartIndexPhp(outfile):
    outfile.write( '<?php $rootdirectory = \'../../\' ?>\n\n' )
    outfile.write( '<html>\n' )
    outfile.write( '<head>\n' )
    outfile.write( '\t<meta http-equiv="Content-Type" content="text/html; charset=utf-8">\n' )
    outfile.write( '\t<title>TV Episodes Downloads</title>\n' )
    outfile.write( '</head>\n\n' )
    outfile.write( '<?php include( \'../../header.php\' ); ?>\n' )
    outfile.write( '<table align="center" width="600"><tr><td>\n\n' )
    outfile.write( '<h1 align=center>TV Episodes Downloads</h1>\n' )
    outfile.write( '<hr>\n\n' )
    outfile.write( '<table align="center" width="600">\n' )
    outfile.write( '\t<tr>\n' )
    outfile.write( '\t\t<th align=center>Episode Name</th>\n' )
    outfile.write( '\t\t<th align=center>MD5SUM</th>\n' )
    outfile.write( '\t</tr>\n' )

def CloseIndexPhp(outfile):
    outfile.write( '</table>\n\n' )
    outfile.write( '<?php include( \'../../footer.php\' ); ?>\n' )
    outfile.write( '</html>\n' )

if __name__ == '__main__':
    with open('index.php', 'w') as outfile:
        StartIndexPhp()
        for f in os.listdir('.'):
            if f == 'index.php' or f.find( '?' ) != -1 or f.find( 'System Volume Information' ) != -1 or f.find( 'RECYCLER' ) != -1:
                continue
            if os.path.isdir(f):
                md5str = hash_utils.md5sum(f)
                print f + ' - ' + md5str
                outfile.write( '\t<tr>\n' )
                outfile.write( '\t\t<td align=center><a href="' + f + '">' + f + '</a></td>\n' )
                outfile.write( '\t\t<td align=center>' + md5str + '</td>\n' )
                outfile.write( '\t</tr>\n' )
        CloseIndexPhp( outfile )
