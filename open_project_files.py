import os, sys, re, Utils, Perforce

def IsProjectFile( file ):
    return not re.search('wsfiles', file, re.I) and re.match(r'^.*\.vcproj$', file, re.I)

if __name__ == '__main__':
    
    for file in Utils.RecurseDirectory( os.getcwd(), IsProjectFile, False ):
        Perforce.OpenForEdit(file)
