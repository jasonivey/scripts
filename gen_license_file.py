import os, string, sys, shutil

if __name__ == '__main__':

    if( len( sys.argv ) < 2 or sys.argv[1].startswith('-') ):
        print 'GenLicenseFile <output file name>'
        sys.exit(1)

    company = raw_input( "Company Name: " )
    serialNumber = raw_input( "Serial Number: " )
    systemCount = raw_input( "System Count: " )
    expireDate = raw_input( "Expiration Date (mm/dd/yyyy): " )
    product = raw_input( "Product Code: " )
    version = raw_input( "Product Version: " )    

    filename = sys.argv[1]
    outfile = file( filename, 'w' )
    outfile.write( "Company Name: " + company + '\n' )
    outfile.write( "Serial Number: " + serialNumber + '\n' )
    outfile.write( "System Count: " + systemCount + '\n' )
    outfile.write( "Expiration Date: " + expireDate + '\n' )
    outfile.write( "Product Code: " + product + '\n' )
    outfile.write( "Product Version: " + version + '\n' )
    outfile.close()

    tmpFileName = '%s.%s' % ( filename, 'tmp' )    
    shutil.copy( filename, tmpFileName )
    
    outfile = file( filename, 'a' )
    outfile.write( '-----Begin Signature-----\n' )
    outfile.close()
    
    os.system( 'openssl sha1 -sign private.key ' + tmpFileName + ' | openssl base64 >> ' + filename )

    outfile = file( filename, 'a' )
    outfile.write( '-----End Signature-----\n' )
    outfile.close()

    os.remove( tmpFileName )

    
        
