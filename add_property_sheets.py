import os, string, shutil, sys, re, p4

perforce = p4.P4()
perforce.connect()

def OpenForEdit( filename ):
    success = len( perforce.run_edit(filename) ) >= 1
    if not success:
        print(('Error while opening %s for edit.' % filename))
    return success

def RecurseDirectory( dir, function ):
    paths = []
    for root, dirs, files in os.walk( dir ):
        for file in files:
            if not function or function(os.path.join( root, file )):
                paths.append( os.path.join( root, file ) )
    return paths


def IsProjectFile( file ):
    return not re.search('wsfiles', file, re.I) and re.match(r'^.*\.vcproj$', file, re.I)


def EnsureConfigIsCorrect(config):
    if config.lower() != 'debug' and config.lower() != 'release':
        assert(False and 'Unknown configuration')


def UpdatePreprocessorDefines(text, config):
    new_text = ''
    index = 0
    for preprocessor in re.finditer(r'(?P<pre>\n\t+PreprocessorDefinitions=")(?P<defines>[^"]+)(?P<post>"\s*\n)', text):
        defines = preprocessor.group('defines')
        defines = defines.replace('WIN32', '')
        defines = defines.replace('_WINDOWS', '')
        if config.lower() == 'debug':
            defines = defines.replace('_DEBUG', '')
        else:
            defines = defines.replace('NDEBUG', '')
        defines = defines.replace(';;', ';').strip(';')
        new_text += text[ index : preprocessor.start() ] + preprocessor.group('pre') + defines + preprocessor.group('post')
        index = preprocessor.end()
    return new_text + text[index:]


def UpdateConfiguration(platform, config, text):
    EnsureConfigIsCorrect(config)
    
    platformName = 'win64-x64' if platform.lower() == 'x64' else 'win32'
    property_sheet = '%s_%s.vsprops' % (platformName, config.lower())
    text = re.sub(r'InheritedPropertySheets="\$\(VCInstallDir\)VCProjectDefaults\\UpgradeFromVC71\.vsprops"', \
                  r'InheritedPropertySheets="$(SolutionDir)%s"' % property_sheet, \
                  text)
    text = re.sub(r'\n\t+OutputDirectory="[^"]+"', '', text)
    text = re.sub(r'\n\t+IntermediateDirectory="[^"]+"', '', text)
    text = re.sub(r'\n\t+UseOfMFC="0"', '', text)
    text = re.sub(r'\n\t+ATLMinimizesCRunTimeLibraryUsage="false"', '', text)
    text = re.sub(r'\n\t+CharacterSet="2"', '', text)

    section_pattern = r'(?P<pre><tool\s+name="%s")(?P<section>.*?)(?P<post>/>)'

    # VCCLCompilerTool Section
    match = re.search(section_pattern % 'VCCLCompilerTool', text, re.I | re.S)
    if match:
        subtext = match.group('section')
        subtext = re.sub(r'\n\t+UseUnicodeResponseFiles="false"', '', subtext)
        subtext = re.sub(r'\n\t+AdditionalIncludeDirectories="[^"]+"', '', subtext)
        subtext = UpdatePreprocessorDefines(subtext, config)
        subtext = re.sub(r'\n\t+PreprocessorDefinitions=""', '', subtext)
        subtext = re.sub(r'\n\t+ExceptionHandling="2"', '', subtext)
        subtext = re.sub(r'\n\t+TreatWChar_tAsBuiltInType="true"', '', subtext)
        subtext = re.sub(r'\n\t+RuntimeTypeInfo="true"', '', subtext)
        subtext = re.sub(r'\n\t+UsePrecompiledHeader="[^"]+"', '', subtext)
        subtext = re.sub(r'\n\t+PrecompiledHeaderFile="[^"]+"', '', subtext)
        subtext = re.sub(r'\n\t+AssemblerListingLocation="[^"]+"', '', subtext)
        subtext = re.sub(r'\n\t+ObjectFile="[^"]+"', '', subtext)
        subtext = re.sub(r'\n\t+ProgramDataBaseFileName="[^"]+"', '', subtext)
        subtext = re.sub(r'\n\t+WarningLevel="[^"]+"', '', subtext)
        subtext = re.sub(r'\n\t+WarnAsError="[^"]+"', '', subtext)
        subtext = re.sub(r'\n\t+SuppressStartupBanner="[^"]+"', '', subtext)
        subtext = re.sub(r'\n\t+DebugInformationFormat="[^"]+"', '', subtext)
        subtext = re.sub(r'\n\t+DisableSpecificWarnings="[^"]+"', '', subtext)
        subtext = re.sub(r'\n\t+ForcedIncludeFiles="pragma.h"', '', subtext)
        subtext = re.sub(r'\n\t+BrowseInformation="0"', '', subtext)
        subtext = re.sub(r'\n\t+ErrorReporting="[^"]+"', '', subtext)
        subtext = re.sub(r'\n\t+MinimalRebuild="[^"]+"', '', subtext)
        if config.lower() == 'debug':
            subtext = re.sub(r'\n\t+Optimization="0"', '', subtext)
            subtext = re.sub(r'\n\t+RuntimeLibrary="1"', '', subtext)
            subtext = re.sub(r'\n\t+EnableFunctionLevelLinking="false"', '', subtext)
            subtext = re.sub(r'\n\t+BasicRuntimeChecks="3"', '', subtext)
        else:
            subtext= re.sub(r'\n\t+Optimization="2"', '', subtext)
            subtext = re.sub(r'\n\t+FavorSizeOrSpeed="1"', '', subtext)
            subtext = re.sub(r'\n\t+StringPooling="true"', '', subtext)
            subtext = re.sub(r'\n\t+RuntimeLibrary="0"', '', subtext)
            subtext = re.sub(r'\n\t+EnableFunctionLevelLinking="true"', '', subtext)
            subtext = re.sub(r'\n\t+BasicRuntimeChecks="0"', '', subtext)
        text = text[ :match.start() ] + match.group('pre') + subtext + match.group('post') + text[ match.end(): ]
    
    # VCResourceCompilerTool Section
    match = re.search(section_pattern % 'VCResourceCompilerTool', text, re.I | re.S)
    if match:
        subtext = match.group('section')
        subtext = re.sub(r'\n\t+Culture="1033"', '', subtext)
        subtext = UpdatePreprocessorDefines(subtext, config)
        subtext = re.sub(r'\n\t+PreprocessorDefinitions=""', '', subtext)
        text = text[ :match.start() ] + match.group('pre') + subtext + match.group('post') + text[ match.end(): ]
    
    # VCLibrarianTool Section
    match = re.search(section_pattern % 'VCLibrarianTool', text, re.I | re.S)
    if match:
        subtext = match.group('section')
        subtext = re.sub(r'\n\t+LinkLibraryDependencies="true"', '', subtext)
        subtext = re.sub(r'\n\t+AdditionalOptions="/Ignore:4006 /Ignore:4221"', '', subtext)
        subtext = re.sub(r'\n\t+SuppressStartupBanner="true"', '', subtext)
        subtext = re.sub(r'\n\t+OutputFile="[^"]+"', '', subtext)
        text = text[ :match.start() ] + match.group('pre') + subtext + match.group('post') + text[ match.end(): ]
    
    # VCMIDLTool Section
    match = re.search(section_pattern % 'VCMIDLTool', text, re.I | re.S)
    if match:
        subtext = match.group('section')
        subtext = re.sub(r'\n\t+TypeLibraryName="[^"]+"', '', subtext)
        subtext = re.sub(r'\n\t+HeaderFileName=""', '', subtext)
        if platform.lower() == 'x64':
            subtext = re.sub(r'\n\t+TargetEnvironment="3"', '', subtext)
        text = text[ :match.start() ] + match.group('pre') + subtext + match.group('post') + text[ match.end(): ]

    # VCLinkerTool Section
    match = re.search(section_pattern % 'VCLinkerTool', text, re.I | re.S)
    if match:
        subtext = match.group('section')
        subtext = re.sub(r'\n\t+AdditionalOptions="/Ignore:4089"', '', subtext)
        subtext = re.sub(r'\n\t+LinkIncremental="[^"]+"', '', subtext)
        subtext = re.sub(r'\n\t+SuppressStartupBanner="true"', '', subtext)
        subtext = re.sub(r'\n\t+GenerateDebugInformation="true"', '', subtext)
        subtext = re.sub(r'\n\t+ProgramDatabaseFile="[^"]+"', '', subtext)
        subtext = re.sub(r'\n\t+GenerateMapFile="true"', '', subtext)
        subtext = re.sub(r'\n\t+MapExports="true"', '', subtext)
        subtext = re.sub(r'\n\t+LargeAddressAware="2"', '', subtext)
        subtext = re.sub(r'\n\t+RandomizedBaseAddress="1"', '', subtext)
        subtext = re.sub(r'\n\t+DataExecutionPrevention="0"', '', subtext)
        subtext = re.sub(r'\n\t+ImportLibrary="[^"]+"', '', subtext)
        subtext = re.sub(r'\n\t+IgnoreDefaultLibraryNames=""', '', subtext)
        subtext = re.sub(r'(\n\t+)OutputFile=".*?(TestRunner2?\.exe)"', r'\1OutputFile="$(OutDir)\\\2"', subtext)
        if not re.search(r'OutputFile=".*?TestRunner2?\.exe"', subtext):
            subtext = re.sub(r'(\n\t+)OutputFile=".*(\.[^"]+)"', '\\1OutputFile="$(OutDir)\$(ProjectName)\\2"', subtext)
            
        if config.lower() == 'debug':
            subtext = re.sub(r'\n\t+EnableCOMDATFolding="0"', '', subtext)
        else:
            subtext = re.sub(r'\n\t+OptimizeReferences="2"', '', subtext)
            subtext = re.sub(r'\n\t+EnableCOMDATFolding="2"', '', subtext)
        
        libdirs = re.search(r'AdditionalLibraryDirectories="(?P<dirs>[^"]+)"', subtext)
        if libdirs:
            dirs = libdirs.group('dirs')
            dirs = re.sub(r'(?:\.\.(?:/|\\))+Boost(?:/|\\)bin(?:/|\\)%s(?:/|\\)?' % platformName, '', dirs)
            subtext = subtext[ :libdirs.start() ] + r'AdditionalLibraryDirectories="' + dirs + '"' + subtext[ libdirs.end(): ]
        subtext = re.sub(r'\n\t+AdditionalLibraryDirectories=""', '', subtext)
        
        if platform.lower() == 'x64':
            subtext = re.sub(r'\n\t+TargetMachine="17"', '', subtext)
        else:
            subtext = re.sub(r'\n\t+TargetMachine="1"', '', subtext)
        text = text[ :match.start() ] + match.group('pre') + subtext + match.group('post') + text[ match.end(): ]

    return text


def UpdateVcProj( filename ):
    print(('Processing %s' % os.path.basename(filename)))
    file = open( filename, 'r' )
    text = file.read()
    file.close()
    orig_text = text
    
    if re.search(r'fileconfiguration', text, re.I):
        print('\tFound file configurations...')
        
    win64_pattern = r'(?:\t+<(?:file)?configuration\s+name="win64 (?:debug|release)\|win32"\s+)(?:.*?)(?:</(?:file)?configuration>\n)'
    if re.search(win64_pattern, text, re.I | re.S):
        print('\tFound legacy IA64 configurations...')
    
    pattern = '(?:\t+<configuration\s+name="(?P<config>debug|release)\|(?P<platform>win32|x64)"\s+)(?:.*?)(?:</configuration>\n)'
    regex = re.compile( pattern, re.I |re.S )
    new_text = ''
    for i in regex.finditer(text):
        if new_text == '':
            new_text = text[: i.start()]
        new_text += UpdateConfiguration(i.group('platform'), i.group('config'), i.group(0))
    new_text += text[i.end():]
    
    if new_text != text and OpenForEdit(filename):
        file = open (filename, 'w')
        file.write(new_text)
        file.close()
    
    
if __name__ == '__main__':
    dir = os.getcwd()
    for filename in RecurseDirectory(dir, IsProjectFile):
        UpdateVcProj(filename)
