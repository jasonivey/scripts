#!/usr/bin/env python

import argparse
import collections
import configparser
import exceptions
import io
from lxml import etree
import os
import pep8
import platform
import string
import sys
import traceback

import bzr_vcs

_VERBOSE_OUTPUT = False
_EXTRA_VERBOSE_OUTPUT = False
_USE_ALTERNATE_ASPECT_PATHS = False

def _get_all_component_aspects(current):
    aspects = []
    for aspect in ['built.linux_x86-64', 'built.win_x64', 'built.osx_universal', 'built.win_32', 'built.linux_i686', 'code']:
        if current != aspect:
            aspects.append(aspect)
    return aspects

def _is_verbose_output_enabled():
    return _VERBOSE_OUTPUT

def _is_extra_verbose_output_enabled():
    return _EXTRA_VERBOSE_OUTPUT

def _use_alternate_aspect_paths():
    return _USE_ALTERNATE_ASPECT_PATHS

def _get_platform_id():
    _u = platform.uname()
    uname = [_u[0], _u[1], _u[2], _u[3], _u[4], _u[5]]
    bitness = '64' if uname[4].find('64') != -1 or uname[5].find('64') != -1 else '32'

    if os.name == 'nt':
        return 'win_x64' if bitness == '64' else 'win_32'
    elif uname[0].startswith('Darwin'):
        return 'osx_universal'
    elif uname[0] == 'Linux':
        return 'linux_x86-64' if bitness == '64' else 'linux_i686'
    else:
        raise exceptions.RuntimeError('Unknown platform encountered: "{0}"'.format(uname[0]))

class Components(dict):
    def __contains__(self, component):
        return str(component) in list(self.keys())

    def has_unparsed_components(self):
        unparsed = [comp for comp in self.values() if not comp.metadata_parsed]
        return len(unparsed) > 0
        
    def get_unparsed_component(self):
        unparsed = [comp for comp in self.values() if not comp.metadata_parsed]
        return unparsed[0]

    def add_component(self, component, container_type=None):
        if str(component) in list(self.keys()):
            if _is_verbose_output_enabled():
                print('Not adding duplicate {0}dependency: {1}'.format(container_type + ' ' if container_type else '', component))
        else:
            if _is_verbose_output_enabled():
                print('Adding {0}dependency: {1}'.format(container_type + ' ' if container_type else '', component))
            self[str(component)] = component
    
class Component(object):
    def __init__(self, name):
        self._name = name
        self._dependencies = Components()
        self._parsed = False

    @property
    def name(self):
        return self._name

    @property
    def metadata_parsed(self):
        return self._parsed

    @metadata_parsed.setter
    def metadata_parsed(self, value):
        self._parsed = value

    @property
    def component_name(self):
        return self._name

    @property
    def dependents(self):
        return self._dependencies

    @dependents.setter
    def dependents(self, value):
        self._dependencies = value

    def display_dependents(self, indent='', sep='\n', output_file=sys.stdout):
        for name, dependent in self.dependents.items():
            print('{0}{1}{2}'.format(indent, name, sep), file=output_file)
            dependent.display_dependents(indent + '  ', sep, output_file)

    def output_xml(self, parent):
        if type(self) is Dependency:
            parent.append(etree.Element('component', name=self.name, component_type='Dependency', branch=self.branch, aspect=self.aspect))
        else:
            assert type(self) is Tool
            parent.append(etree.Element('component', name=self.name, component_type='Tool', tool_type=self.tool_type, version=self.version))

    def output_dependents_xml(self, parent):
        components = list(self.dependents.values())
        components.sort(key=lambda component: component.name.lower())
        for dependent in components:
            dependent.output_xml(parent)
            dependent.output_dependents_xml(parent[-1])

    def __str__(self):
        return self._name

    def __eq__(self, other):
        return self._name == other._name

class Dependency(Component):
    def __init__(self, branch, name, aspect):
        Component.__init__(self, name)
        self._branch = branch
        self._aspect = aspect
        self._set_component_name()

    def _set_component_name(self):
        self._component_name = '{0}/{1}/{2}'.format(self._branch, self._name, self._aspect)

    @property
    def branch(self):
        return self._branch

    @property
    def aspect(self):
        return self._aspect

    @aspect.setter
    def aspect(self, value):
        self._aspect = value
        self._set_component_name()

    @property
    def component_name(self):
        return self._component_name

    def __str__(self):
        return self.component_name

    def __eq__(self, other):
        return self.component_name == other.component_name

class Tool(Component):
    def __init__(self, name, value, tool_type):
        Component.__init__(self, name)
        self._value = value
        self._tool_type = tool_type
        self._component_name = '{0}-{1}'.format(self.name, self.version)
        self.metadata_parsed = True

    @property
    def component_name(self):
        return self._component_name

    @property
    def version(self):
        return self._value.split(',')[0].strip()

    @property
    def tool_type(self):
        return self._tool_type
    
    def __str__(self):
        return self._component_name

    def __eq__(self, other):
        return self.component_name == other.component_name

class DependencyWalker(object):
    def __init__(self, component, depth, built_aspect=None, output_file=sys.stdout):
        self._component = component
        self._depth = depth
        self._built_aspect = built_aspect if built_aspect else _get_platform_id()
        self._dependencies = Components()
        self._output_file = output_file

    @property
    def root_component(self):
        return self._component

    @property
    def max_depth(self):
        return self._depth

    def is_max_depth_reached(self, depth):
        return depth >= self.max_depth

    @property
    def dependents_list(self):
        return self._dependencies
    
    @property
    def output_file(self):
        return self._output_file

    def _get_aspect(self, aspect):
        return '{0}.{1}'.format(aspect, self._built_aspect) if aspect == 'built' else aspect

    @staticmethod
    def _get_metadata_section(metadata, section_name):
        try:
            return metadata.items(section_name)
        except configparser.NoSectionError:
            return None

    def _parse_components(self, metadata, component):
        component_dependencies = DependencyWalker._get_metadata_section(metadata, 'component dependencies')
        if not component_dependencies:
            return
        for name, aspect in component_dependencies:
            dependent = Dependency(component.branch, name, self._get_aspect(aspect.strip(' ,')))
            component.dependents.add_component(dependent, 'component')

    def _parse_tools(self, metadata, component):
        for section in ['build tools', 'test tools', 'run tools']:
            tools = DependencyWalker._get_metadata_section(metadata, section)
            if tools:
                for name, value in tools:
                    component.dependents.add_component(Tool(name, value, section.split(' ')[0]), 'component')

    @staticmethod
    def _read_metadata(component):
        component.metadata_parsed = True
        if _is_verbose_output_enabled():
            print('Reading: {0}/metadata.txt'.format(component))
        metadata = bzr_vcs.cat('{0}/metadata.txt'.format(component))
        if not metadata:
            print('INFO: {0} not found'.format(component))
            return None
        else:
            if _is_extra_verbose_output_enabled():
                print('\nFile: {0}/metadata.txt\n{1}\n'.format(component, metadata))
            config = configparser.SafeConfigParser()
            config.optionxform = str
            config.readfp(io.BytesIO(metadata))
            return config

    def _update_dependents(self, component):
        for dependent_name, dependent in component.dependents.items():
            assert dependent_name in self.dependents_list
            master_dependent = self.dependents_list[dependent_name]
            dependent.dependents = master_dependent.dependents
            self._update_dependents(dependent)

    def walk(self):
        depth = 0
        root_metadata = self._read_metadata(self.root_component)
        for aspect in _get_all_component_aspects(self.root_component.aspect):
            if root_metadata or not _use_alternate_aspect_paths():
                break
            self.root_component.aspect = aspect
            root_metadata = self._read_metadata(self.root_component)
        if not root_metadata:
            print('ERROR: Unable to read the root metadata.txt file.')
            print('       Is it possible the path used is not in the')
            print('       form "branch/component-name/aspect"?')
            return False

        self._parse_components(root_metadata, self.root_component)
        self._parse_tools(root_metadata, self.root_component)
        for dependent in self.root_component.dependents.values():
            self.dependents_list.add_component(dependent, 'sandbox')

        while self.dependents_list.has_unparsed_components():
            if self.is_max_depth_reached(depth + 1):
                break
            else:
                depth = depth + 1
            component = self.dependents_list.get_unparsed_component()
            metadata = self._read_metadata(component)
            for aspect in _get_all_component_aspects(component.aspect):
                if metadata or not _use_alternate_aspect_paths():
                    break
                component.aspect = aspect
                metadata = self._read_metadata(component)
            if metadata:
                self._parse_components(metadata, component)
                self._parse_tools(metadata, component)
                for dependency in component.dependents.values():
                    self.dependents_list.add_component(dependency, 'sandbox')
            else:
                print('ERROR: Unable to read {0} metadata.txt file.'.format(component))

        self._update_dependents(self.root_component)
        return True

    def _get_components_from_all(self):
        components = []
        for name, component in self.dependents_list.items():
            if type(component) is Dependency:
                components.append(component)
        components.sort(key=lambda component: component.name.lower())
        return components

    def _get_tool_from_all(self):
        tools = []
        for name, component in self.dependents_list.items():
            if type(component) is Tool:
                tools.append(component)
        tools.sort(key=lambda tool: tool.name.lower())
        return tools

    def _display_list_xml(self):
        root = etree.Element("components")

        if type(self.root_component) is Tool:
            root.append(etree.Element('component', name=self.root_component.name, component_type='Tool', tool_type=self.root_component.tool_type, version=self.root_component.version))
        else:
            root.append(etree.Element('component', name=self.root_component.name, component_type='Dependency', branch=self.root_component.branch, aspect=self.root_component.aspect))

        for component in self._get_components_from_all():
            root.append(etree.Element('component', name=component.name, component_type='Dependency', branch=component.branch, aspect=component.aspect))

        for tool in self._get_tool_from_all():
            root.append(etree.Element('component', name=tool.name, component_type='Tool', tool_type=tool.tool_type, version=tool.version))

        xml_declaration = '<?xml version="1.0" encoding="UTF-8" ?>'
        xml_body = etree.tostring(root, pretty_print=True)
        print('{0}\n{1}'.format(xml_declaration, xml_body), file=self.output_file)

    def _display_list_text(self):
        print('\nDependency list ({0}):'.format(self.root_component), file=self.output_file)
        for component in self._get_components_from_all():
            print('  {0}'.format(name), file=self.output_file)

        print('\nTools list ({0}):'.format(self.root_component), file=self.output_file)
        for tool in self._get_tool_from_all():
            print('  {0}'.format(tool.name), file=self.output_file)

    def display_list(self, output_type='text'):
        if output_type == 'text':
            self._display_list_text()
        elif output_type == 'xml':
            self._display_list_xml()

    def _display_ancestry_xml(self):
        root = etree.Element("components")
        self.root_component.output_xml(root)
        self.root_component.output_dependents_xml(root[-1])

        xml_declaration = '<?xml version="1.0" encoding="UTF-8" ?>'
        xml_body = etree.tostring(root, pretty_print=True)
        print('{0}\n{1}'.format(xml_declaration, xml_body), file=self.output_file)

    def _display_ancestry_text(self):
        print('\nAncestry list:', file=self.output_file)
        print('{0}'.format(self.root_component), file=self.output_file)
        self.root_component.display_dependents(indent='  ', output_file=self.output_file)

    def display_ancestry(self, output_type='text'):
        if output_type == 'text':
            self._display_ancestry_text()
        elif output_type == 'xml':
            self._display_ancestry_xml()
    

def _parse_args():
    parser = argparse.ArgumentParser(description='Traverse the metadata.txt files to find all component and tool dependencies')
    action_group = parser.add_mutually_exclusive_group(required=True)
    action_group.add_argument('-a', '--ancestry', default=False, dest='ancestry', action='store_true', help='display a hierarchy of component dependencies')
    action_group.add_argument('-l', '--list', default=False, dest='flat_list', action='store_true', help='display a flat list of all the component dependencies')
    
    parser.add_argument(metavar='PATH', dest='path', help='path to component (i.e. v42_release/webapp/code)')
    parser.add_argument('-b', '--use-built', metavar='TYPE', dest='built_aspect', required=False, help='change the component aspect queried from the current OS to \'win_x64\', \'win_32\', \'linux_x86-64\', \'linux_i686\' or \'osx_universal\'')
    parser.add_argument('-f', '--file', metavar='FILE', dest='output_file', default=sys.stdout, type=argparse.FileType('w'), required=False, help='file to redirect the output')
    parser.add_argument('-d', '--depth', default=999, type=int, required=False, help='the max levels to query through metadata.txt files (infinite=999)')
    parser.add_argument('-t', '--type', metavar='TYPE', dest='output_type', default='text', required=False, help='output type (either \'text\' or \'xml\')')
    parser.add_argument('-u', '--use-alternate', default=False, action='store_true', help='automatically use alternate aspect when metadata.txt isn\'t found')
    parser.add_argument('-v', '--verbose', default=False, action='store_true', help='show verbose output')
    parser.add_argument('-vv', '--extra-verbose', default=False, action='store_true', help='show extra verbose output')

    args = parser.parse_args()

    global _VERBOSE_OUTPUT
    global _EXTRA_VERBOSE_OUTPUT
    global _USE_ALTERNATE_ASPECT_PATHS

    _VERBOSE_OUTPUT = args.verbose
    _EXTRA_VERBOSE_OUTPUT = args.extra_verbose
    _USE_ALTERNATE_ASPECT_PATHS = args.use_alternate
    
    if args.output_type.lower().find('xml') != -1:
        output_type = 'xml'
    else:
        output_type = 'text'

    return args.path, args.built_aspect, output_type, args.output_file, args.flat_list, args.ancestry, args.depth

def main():
    path, built_aspect, output_type, output_file, flat_list, ancestry, depth = _parse_args()
    try:
        dirs = path.replace('\\', '/').split('/')
        assert len(dirs) == 3
        root_dependency = Dependency(dirs[0], dirs[1], dirs[2])
        walker = DependencyWalker(root_dependency, depth, built_aspect, output_file)
        if not walker.walk():
            return 1
        if flat_list:
            walker.display_list(output_type)
        else:
            walker.display_ancestry(output_type)
        output_file.close()
        return 0
    except:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stdout)
        return 1

if __name__ == '__main__':
	sys.exit(main())
