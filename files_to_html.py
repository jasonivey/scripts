import os, string, shutil, time
from stat import *

def CompareIgnoreCase( x, y ):
    return cmp( x.lower(), y.lower() )

def CreateHtml( name, dir ):
    print '.'

    dir = dir.replace( 'media/', '' )
    if dir == 'media':
        dir = 'mediahtml'
    
    outfile = file( 'mediahtml/' + name, 'w' )
    
    outfile.write( '<?php\n' )
    outfile.write( 'session_start();\n' )
    outfile.write( '$_SESSION[\'sourcefile\'] = \'' + name + '\';\n' )
    outfile.write( 'require(\'inc/header.inc.php\');\n' )
    outfile.write( 'require(\'inc/auth.inc.php\');\n\n' )
    outfile.write( '$rootdirectory = \'../\';\n' )
    outfile.write( '?>\n\n' )
    
    outfile.write( '<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN">\n\n' )
    
    outfile.write( '<html><head><title>' + dir + '</title></head>\n\n' )
    outfile.write( '<?php include( $rootdirectory . \'header.php\' ); ?>' )
    
    outfile.write( '<h3 align="center">' + dir + '</h3>\n\n' )

    outfile.write( '<table width="600" align="center" cellpadding="5" cellspacing="0" border="1">\n' )
    
    outfile.write( '<tr>\n' )
    outfile.write( '\t<th align="left" width="88%">Name</th>\n' )
    outfile.write( '\t<th align="left" width="12%">Size</th>\n' )
    outfile.write( '</tr>\n' )
    return outfile


def CloseHtml( outfile ):
    outfile.write( '</table>\n\n' )
    outfile.write( '<?php include( $rootdirectory . \'footer.php\' ); ?>\n\n' )
    outfile.write( '</html>\n' )
    outfile.close()
    
    
def RecurseDirectory( dir, name, count ):

    directories = []
    files = []
    dirs = {}
    outfile = CreateHtml( name, dir )
    
    for f in os.listdir( dir ):
        if f.find( '?' ) != -1:
            continue

        pathname = '%s/%s' % ( dir, f )
        mode = os.stat( pathname ).st_mode

        if S_ISDIR( mode ):
            directories.append( f )
        else:
            files.append( f )

    directories.sort( CompareIgnoreCase )
    for directory in directories:
        dirs[count] = '%s/%s' % ( dir, directory )
        bytes = os.stat( dirs[count] ).st_size        
        
        outfile.write( '<tr>\n' )
        outfile.write( '\t<td><img src="folder.gif"><a href=\"' + ('dir%d.php' % count) + '\">' + directory + '</a></td>\n' )
        ##outfile.write( '\t<td>%s</td>\n' % time.strftime( '%d-%b-%Y %H:%M', time.localtime(access) ) )
        outfile.write( '\t<td>%d Mb</td>\n' % ( bytes / 1048576 ) )
        outfile.write( '</tr>\n' )        
        count = count + 1

    files.sort( CompareIgnoreCase )
    for file in files:
        filename = '%s/%s' % ( dir, file )
        bytes = os.stat( filename ).st_size
        
        outfile.write( '<tr>\n' )
        if( file.lower().endswith( '.mp3' ) ):
            outfile.write( '\t<td><img src="sound2.gif"><a href=\"/' + filename + '\">' + file + '</a></td>\n' )
        else:
            outfile.write( '\t<td><img src="movie.gif"><a href=\"/' + filename + '\">' + file + '</a></td>\n' )
            
        ##outfile.write( '\t<td>%s</td>\n' % time.strftime( '%d-%b-%Y %H:%M', time.localtime(access) ) )
        outfile.write( '\t<td>%d Mb</td>\n' % ( bytes / 1048576 ) )
        outfile.write( '</tr>\n' )
        
    CloseHtml( outfile )

    keys = dirs.keys()
    keys.sort()
    for k in keys:
        count = RecurseDirectory( dirs[k], ('dir%d.php' % k), count )

    return count    
    

if __name__ == '__main__':
    ##os.mkdir( 'mediahtml' )
    RecurseDirectory( 'media', 'index.php', 1 )
