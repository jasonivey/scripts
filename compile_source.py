#!/usr/bin/env python
from __future__ import print_function
import argparse
import os
import sys
import re
import subprocess
import traceback
import uuid

def enum(**enums):
    return type('Enum', (), enums)

Verbosity = enum(ERROR=0, INFO=1, DEBUG=2, TRACE=3)

_VERBOSE_LEVEL = 0

def get_verbosity(verbosity):
    if verbosity == Verbosity.ERROR:
        return 'ERROR'
    if verbosity == Verbosity.INFO:
        return 'INFO'
    if verbosity == Verbosity.DEBUG:
        return 'DEBUG'
    if verbosity == Verbosity.TRACE:
        return 'TRACE'
    return None

def verbose_print(verbosity, msg):
    if verbosity > _VERBOSE_LEVEL:
        return
    print('{0}: {1}'.format(get_verbosity(verbosity), msg))

def _is_valid_file(filename):
    if not os.path.isfile(filename):
        msg = '{0} is not a valid file name'.format(filename)
        raise argparse.ArgumentTypeError(msg)
    else:
        return os.path.abspath(filename)

def _is_valid_source(source):
    if not os.path.exists(source):
        msg = '{0} is not a valid path'.format(source)
        raise argparse.ArgumentTypeError(msg)
    else:
        return os.path.abspath(source)

def _parse_args():
    description = 'Compile a source file or a directory of source files'
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('-c', '--compiler', metavar='<compiler>', required=True, help='name of compiler (gcc/g++/clang++)')
    parser.add_argument('-l', '--stdlib', metavar='<stdlib>', default='libstdc++', help='the standard library to use (libstdc++ or libc++)')
    parser.add_argument('-v', '--verbose', action='count', default=0, help='output verbose debugging information')
    parser.add_argument('-p', '--preprocessor', default=False, action='store_true', help='compile the source into preprocessed text')
    parser.add_argument('-f', '--option-file', type=_is_valid_file, help='path to .clang_complete file style file')
    parser.add_argument('-o', '--option', nargs='*', help='specify an option to be passed to the compiler')
    parser.add_argument('-k', '--keep', default=False, action='store_true', help='keep the generated source file when compiling header')
    parser.add_argument('-b', '--break', dest='break_on_error', default=False, action='store_true', help='stop the compile after the first error')
    parser.add_argument('source', type=_is_valid_source, nargs='+', help='source file or directory')
    args = parser.parse_args()
    global _VERBOSE_LEVEL
    _VERBOSE_LEVEL = args.verbose
    verbose_print(Verbosity.INFO, 'compiler: {0}, standard library: {1}, verbose: {2}, preprocessor: {3}, option-file: {4}, options: {5}, keep: {6}, break: {7}, source: {8}' \
            .format(args.compiler, args.stdlib, args.verbose, args.preprocessor, args.option_file, args.option, args.keep, args.break_on_error, args.source))
    return args.compiler, args.stdlib, args.preprocessor, args.option_file, args.option, args.keep, args.break_on_error, args.source

def _is_source_file(filename):
    return filename.lower().endswith('.c') or \
           filename.lower().endswith('.cc') or \
           filename.lower().endswith('.cp') or \
           filename.lower().endswith('.cxx') or \
           filename.lower().endswith('.cpp') or \
           filename.lower().endswith('.c++') or \
           _is_header_file(filename)

def _is_header_file(filename):
    return filename.lower().endswith('.h') or \
           filename.lower().endswith('.hh') or \
           filename.lower().endswith('.hxx') or \
           filename.lower().endswith('.hpp') or \
           filename.lower().endswith('.h++') or \
           filename.lower().endswith('.inl') or \
           filename.lower().endswith('.ii') or \
           filename.lower().endswith('.ixx') or \
           filename.lower().endswith('.ipp') or \
           filename.lower().endswith('.txx') or \
           filename.lower().endswith('.tpp') or \
           filename.lower().endswith('.tpl')

def _get_all_sources(sources):
    verbose_print(Verbosity.DEBUG, 'identifing all the files to compile')
    all_sources = []
    for source in sources:
        if os.path.isfile(source):
            verbose_print(Verbosity.TRACE, 'adding %s as a file to compile' % source)
            all_sources.append(source)
        else:
            verbose_print(Verbosity.TRACE, 'interpreting %s as a directory' % source)
            for root, dirs, files in os.walk(source):
                for file_name in files:
                    if _is_source_file(file_name):
                        verbose_print(Verbosity.TRACE, 'adding %s as a file to compile' % source)
                        all_sources.append(os.path.join(root, file_name))
    return all_sources

class Compiler(object):
    def __init__(self, compiler, stdlib=None, preprocessor=False, options_file=None, options=None, keep=False):
        self._compiler = compiler
        self._options = ['-std=c++11']
        self._preprocessor = preprocessor
        self._keep = keep
        self._errors = None
        if stdlib and stdlib != 'libstdc++':
            self._options.append('-stdlib={0}'.format(stdlib))
        if self._preprocessor:
            self._options.append('-E')
            self._options.append('-C')
            self._options.append('-P')
        if options_file:
            self._parse_compiler_options(options_file)
        if options:
            for option in options:
                self._options.append(option)
        verbose_print(Verbosity.INFO, 'options: %s' % self._options)

    def _remove_option(self, option):
        verbose_print(Verbosity.INFO, 'removing option %s' % option)
        name = None
        for opt in self._options:
            if opt.startswith(option):
                name = opt
                break
        if name:
            self._options.remove(name)

    def _parse_compiler_options(self, filename):
        with open(filename, 'r') as f:
            lines = f.readlines()
        for line in lines:
            option = line.strip()
            verbose_print(Verbosity.DEBUG, 'adding option: %s' % option)
            if option.startswith('-std='):
                #self._remove_option('-std=')
                continue
            if option.startswith('-stdlib='):
                #self._remove_option('-stdlib=')
                continue
            if option.startswith('-iquote'):
                option = '-iquote{0}'.format(os.path.abspath(os.path.join(os.path.dirname(filename), option[7:])))
            if option.startswith('-I'):
                option = '-I{0}'.format(os.path.abspath(os.path.join(os.path.dirname(filename), option[2:])))
            self._options.append(option)

    #def add_include_path(self, path):
    #    self._options.append('-I{0}'.format(os.path.abspath(path)))

    @property
    def errors(self):
        return self._errors

    @property
    def options(self):
        return ' '.join(self._options)

    def _get_output_option(self, filename):
        if self._preprocessor:
            basename = os.path.splitext(filename)[0]
            return '-o {0}.i'.format(basename)
        else:
            return '-o /dev/stdout'

    def _get_options_updating_includes(self, filename):
        dirname = os.path.dirname(filename)
        options = ''
        for option in self._options:
            if option.startswith('-iquote'):
                #options += '-iquote./{0} '.format(os.path.relpath(option[7:], dirname))
                options += option + ' ' 
            elif option.startswith('-I'):
                #options += '-I./{0} '.format(os.path.relpath(option[2:], dirname))
                options += option + ' ' 
            else:
                options += option + ' '
        return options.strip()

    def _create_source_file(self, filename):
        maincpp = '/tmp/{0}-main.cpp'.format(uuid.uuid1())
        verbose_print(Verbosity.DEBUG, 'creating source file %s' % maincpp)
        with open(maincpp, 'w') as file:
            file.write('#include "{0}"\n'.format(filename))
            file.write('\n\n')
            file.write('int main(int, char **) {\n')
            file.write('    return 0;\n')
            file.write('}\n')
        return maincpp

    def compile_file(self, filename):
        if _is_header_file(filename):
            return self.compile_header(filename)
        else:
            return self.compile_source(filename)

    def compile_header(self, filename):
        verbose_print(Verbosity.INFO, 'compiling header %s' % filename)
        source = self._create_source_file(filename)
        retval = self.compile_source(source)
        if not self._keep:
            verbose_print(Verbosity.INFO, 'deleting source file %s' % source)
            os.remove(source)
        return retval

    def compile_source(self, filename):
        verbose_print(Verbosity.INFO, 'compiling source %s' % filename)
        self._options.append(self._get_output_option(filename))
        command = '{0} {1} -c {2}'.format(self._compiler, self._get_options_updating_includes(filename), filename)
        verbose_print(Verbosity.INFO, 'command: %s' % command)
        process = subprocess.Popen(command, shell=True, bufsize=1, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        stdoutdata, stderrdata = process.communicate()
        if process.wait() != 0:
            self._errors = stderrdata.decode('utf-8')
            return False
        else:
            return True

    def compile_str(self, str_buffer):
        pass


def main():
    compiler_name, stdlib, preprocessor, option_file, options, keep, break_on_error, sources = _parse_args()

    failed = False
    try:
        compiler = Compiler(compiler_name, stdlib, preprocessor, option_file, options, keep)
        for source in _get_all_sources(sources):
            if compiler.compile_file(source):
                print('%s -- success' % source)
            else:
                print('%s -- failure\n%s' % (source, compiler.errors))
                failed = True
            if failed and break_on_error:
                break
    except:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stdout)
        return 1

    return 0 if not failed else 1

if __name__ == '__main__':
    sys.exit(main())

