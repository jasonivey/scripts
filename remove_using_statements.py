#!/usr/bin/env python
# vim:softtabstop=4:ts=4:sw=4:expandtab:tw=120

import argparse
import os
import re
import sys
import traceback

def _parse_args():
    #description = 'Update header files to remove all using statements'
    #parser = argparse.ArgumentParser(description=description)
    # parser.add_argument('-c', '--compiler', metavar='<compiler>', required=True, help='name of compiler (gcc/g++/clang++)')
    # parser.add_argument('-l', '--stdlib', metavar='<stdlib>', default='libstdc++', help='the standard library to use (libstdc++ or libc++)')
    # parser.add_argument('-v', '--verbose', action='count', default=0, help='output verbose debugging information')
    # parser.add_argument('-p', '--preprocessor', default=False, action='store_true', help='compile the source into preprocessed text')
    # parser.add_argument('-f', '--option-file', type=_is_valid_file, help='path to .clang_complete file style file')
    # parser.add_argument('-o', '--option', nargs='*', help='specify an option to be passed to the compiler')
    # parser.add_argument('-k', '--keep', default=False, action='store_true', help='keep the generated source file when compiling header')
    # parser.add_argument('-b', '--break', dest='break_on_error', default=False, action='store_true', help='stop the compile after the first error')
    # parser.add_argument('source', type=_is_valid_source, nargs='+', help='source file or directory')
    #args = parser.parse_args()
    #global _VERBOSE_LEVEL
    # _VERBOSE_LEVEL = args.verbose
    # verbose_print(Verbosity.INFO, 'compiler: {0}, standard library: {1}, verbose: {2}, preprocessor: {3}, option-file: {4}, options: {5}, keep: {6}, break: {7}, source: {8}' \
    #         .format(args.compiler, args.stdlib, args.verbose, args.preprocessor, args.option_file, args.option, args.keep, args.break_on_error, args.source))
    # return args.compiler, args.stdlib, args.preprocessor, args.option_file, args.option, args.keep, args.break_on_error, args.source
    return

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

def _get_header_files(dir):
    all_headers = []
    for root, dirs, files in os.walk(dir):
        for file_name in files:
            fullpath = os.path.join(root, file_name)
            if _is_header_file(fullpath) and fullpath.find('/external/') == -1:
                #print('adding %s as a file to update' % fullpath)
                all_headers.append(fullpath)
    return all_headers

_containers = ['shared_ptr',
               'unique_ptr',
               'weak_ptr',
               'enable_shared_from_this',
               'static_pointer_cast',
               'dynamic_pointer_cast',
               'const_pointer_cast',
               'reinterpret_pointer_cast',
               'vector',
               'array',
               'pair',
               'tuple',
               'tie',
               'deque',
               'forward_list',
               'list',
               'set',
               'map',
               'multiset',
               'multimap',
               'unordered_set',
               'unordered_map',
               'unordered_multiset',
               'unordered_multimap',
               'stack',
               'queue',
               'priority_queue',]
_algorithms = ['all_of',
              'any_of',
              'none_of',
              'for_each',
              'for_each_n',
              'count',
              'count_if',
              'mismatch',
              'find',
              'find_if',
              'find_if_not',
              'find_end',
              'find_first_of',
              'adjacent_find',
              'search',
              'search_n',
              'copy',
              'copy_if',
              'copy_n',
              'copy_backward',
              'move',
              'move_backward',
              'fill',
              'fill_n',
              'transform',
              'generate',
              'generate_n',
              'remove',
              'remove_if',
              'remove_copy',
              'remove_copy_if',
              'replace',
              'replace_if',
              'replace_copy',
              'replace_copy_if',
              'swap',
              'swap_ranges',
              'iter_swap',
              'reverse',
              'reverse_copy',
              'rotate',
              'rotate_copy',
              'shift_left',
              'shift_right',
              'random_shuffle',
              'shuffle',
              'sample',
              'unique',
              'unique_copy',
              'is_partitioned',
              'partition',
              'partition_copy',
              'stable_partition',
              'partition_point',
              'is_sorted',
              'is_sorted_until',
              'sort',
              'partial_sort',
              'partial_sort_copy',
              'stable_sort',
              'nth_element',
              'lower_bound',
              'upper_bound',
              'binary_search',
              'equal_range',
              'merge',
              'inplace_merge',
              'includes',
              'set_difference',
              'set_intersection',
              'set_symmetric_difference',
              'set_union',
              'is_heap',
              'is_heap_until',
              'make_heap',
              'push_heap',
              'pop_heap',
              'sort_heap',
              'max',
              'max_element',
              'min',
              'min_element',
              'minmax',
              'minmax_element',
              'clamp',
              'equal',
              'lexicographical_compare',
              'compare_3way',
              'lexicographical_compare_3way',
              'is_permutation',
              'next_permutation',
              'prev_permutation',
              'iota',
              'accumulate',
              'inner_product',
              'adjacent_difference',
              'partial_sum',
              'reduce',
              'exclusive_scan',
              'inclusive_scan',
              'transform_reduce',
              'transform_exclusive_scan',
              'transform_inclusive_scan',
              'uninitialized_copy',
              'uninitialized_copy_n',
              'uninitialized_fill',
              'uninitialized_fill_n',
              'uninitialized_move',
              'uninitialized_move_n',
              'uninitialized_default_construct',
              'uninitialized_default_construct_n',
              'uninitialized_value_construct',
              'uninitialized_value_construct_n',
              'destroy_at',
              'destroy',
              'destroy_n',
              'qsort',
              'bsearch',]

_functions = ['make_shared',
              'make_unique',
              'make_pair',
              'make_tuple',
              'begin',
              'end',
              'cbegin',
              'cend',
              'rbegin',
              'crbegin'
              'rend',
              'crend']

def _update_functions(data):
    functions = '|'.join(_functions)
    return re.sub(r'(?<!::)(?P<obj>(' + functions + ')\s*[\({<])', r'std::\g<obj>', data)
    
def _update_algorithms(data):
    algorithms = '|'.join(_algorithms)
    return re.sub(r'(?<!::)(?P<obj>(' + algorithms + ')\s*\()', r'std::\g<obj>', data)
                  
def _update_containers(data):
    containers = '|'.join(_containers)
    return re.sub(r'(?<!::)(?P<obj>(' + containers + ')<)', r'std::\g<obj>', data)

def _update_string(data):
    new_data = []
    for line in data.split('\n'):
        if line.find('#include') != -1:
            new_data.append(line)
        else:
            line = re.sub(r'(?<!::)(?P<obj>(string|string_view))', r'std::\g<obj>', line)
            new_data.append(line)
    return '\n'.join(new_data)

def _process_header(filepath):
    #print('file name: %s' % filepath)
    with open(filepath, 'r') as f:
        data = f.read()

    # Relocated code
    updated_data = _update_string(data)
    updated_data = _update_containers(updated_data)
    ###updated_data = _update_algorithms(updated_data)
    updated_data = _update_functions(updated_data)
    ###updated_data = re.sub(r'(?P<using>using namespace jsrl;)', r'//\g<using>', data)

    if updated_data != data:
        with open(filepath, 'w') as f:
            f.write(updated_data)
        return True
    return False

def _process_headers(filepath):
    headers = []
    if os.path.isdir(filepath):
        headers = _get_header_files(filepath)
    else:
        headers.append(os.path.abspath(sys.argv[1]))

    for header in headers:
        if _process_header(header):
            print('UPDATED    -- %s' % header)
        else:
            print('NON-UPATED -- %s' % header)
        
    
def main():
    _parse_args()

    try:
        if len(sys.argv) > 1:
            _process_headers(sys.argv[1])
        else:
            _process_headers(os.getcwd())
    except:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stdout)
        return 1
    return 0

if __name__ == '__main__':
    sys.exit(main())