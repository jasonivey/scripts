#!/usr/bin/env python
import os
import sys
import re
import string


class ProjectDependency:
    def __init__(self, raw_dependency):
        match = re.match(r'^(?P<Project>{[^}]+}) = (?P<Parent>{[^}]+})$', raw_dependency)
        self.Guid = match.group('Project')
        self.ParentGuid = match.group('Parent')

    def __cmp__(self, other):
        return cmp(self.Guid.lower(), other.Guid.lower())


class Project:
    def __init__(self, guid, name, parent, project, data):
        self.Guid = guid
        self.Name = name
        self.Parent = parent
        self.Project = project
        self.Data = data
        self.ParentGuid = None
        self.ChildGuids = []
        self.Children = []

    def AddHierarchyGuids(self, dependencies):
        count = dependencies.count(self)
        if count > 0:
            index = dependencies.index(self)
            assert( count == 1 and index != -1 )
            self.ParentGuid = dependencies[index].ParentGuid

        for dependency in dependencies:
            if self.Guid.lower() == dependency.ParentGuid.lower():
                self.ChildGuids.append(dependency.Guid)

    def AddChildProjects(self, projects):
        for childGuid in self.ChildGuids:
            assert( childGuid in projects )
            self.Children.append(projects[childGuid])
        for child in self.Children:
            child.AddChildProjects(projects)
        self.Children.sort(lambda x, y: cmp(x.Name.lower(), y.Name.lower()))

    def __cmp__(self, other):
        return cmp(self.Guid.lower(), other.Guid.lower())
    
    #def __eq__(self, other):
    #    return self.Guid.lower() == other.Guid.lower()
        
    def DumpToText(self):
        project_text = 'Project("%s") = "%s", "%s", "%s"' % (self.Parent, self.Name, self.Project, self.Guid)
        project_text += self.Data + 'EndProject\n'
        dependencies_text = '\t\t%s = %s\n' % (self.Guid, self.ParentGuid) if self.ParentGuid else ''
        for child in self.Children:
            child_project_text, child_dependencies_text = child.DumpToText()
            project_text += child_project_text
            dependencies_text += child_dependencies_text
        return project_text, dependencies_text


class Solution:
    def __init__(self, data):
        self.Data = data
        self.Projects = {}
        self._ParseProjectDefinitions()
        self._ParseProjectDependencies()

    def GetProjectDefinitionsText(self):
        text = ''
        for project in self.Projects.values():
            text += str(project)
        return text
    
    def _ParseProjectDefinitions(self):
        project_pattern = r'Project\("(?P<Parent>{[^}]+})"\)\s*=\s*"(?P<Name>[^"]+)"\s*,\s*"(?P<Project>[^"]*)"\s*,\s*"(?P<Guid>{[^}]+})"(?P<Data>\s*.*?)EndProject\n'
        find_project_regex = re.compile(project_pattern, re.S)
    
        for match in find_project_regex.finditer(self.Data):
            project = Project(match.group('Guid'), match.group('Name'), match.group('Parent'), match.group('Project'), match.group('Data'))
            assert(match.group('Guid') not in self.Projects)
            self.Projects[match.group('Guid')] = project

    def _ParseProjectDependencies(self):
        project_dependencies_pattern = r'GlobalSection\(NestedProjects\) = preSolution\n(?P<Dependencies>.*?)EndGlobalSection\n'
        match = re.search(project_dependencies_pattern, self.Data, re.S)
        
        # split the string into an array, remove the tabs on the start of the strings and then remove (filter) the empty array elements
        raw_dependencies = filter(lambda value: len(value) != 0, map(string.strip, match.group('Dependencies').split('\n')))
        dependencies = []
        for raw_dependency in raw_dependencies:
            dependencies.append(ProjectDependency(raw_dependency))
    
        for project in iter(self.Projects.values()):
            project.AddHierarchyGuids(dependencies)

        # Reduce the project list down to only those with no parent (root nodes)
        projects = filter(lambda project: not project.ParentGuid, self.Projects.values())
        for project in projects:
            project.AddChildProjects(self.Projects)

        # Now that all the children are all hooked up replace our list with only root nodes
        self.Projects = projects
        self.Projects.sort(lambda x, y: cmp(x.Name.lower(), y.Name.lower()))

    def __str__(self):
        project_text = ''
        dependencies_text = ''
        for project in self.Projects:
            project_text_tmp, dependencies_text_tmp = project.DumpToText()
            project_text += project_text_tmp
            dependencies_text += dependencies_text_tmp
            
        text = self.Data
        
        replace_projects_regex = re.compile(r'\nProject\(".*EndProject\n', re.S)
        text = replace_projects_regex.sub('PROJECTS_HERE', text)
        text = text.replace('PROJECTS_HERE', '\n%s' % project_text)
        
        #project_dependencies_regex = re.compile(r'(GlobalSection\(NestedProjects\) = preSolution).*?(\tEndGlobalSection\n)', re.S)
        #text = project_dependencies_regex.sub('\\1DEPENDENCIES_HERE\\2', text)
        #text = text.replace('DEPENDENCIES_HERE', '\n%s' % dependencies_text)
        return text


if __name__ == '__main__':
    input_name = None
    output_name = None
    if len(sys.argv) < 2:
        print('ERROR: invalid command line\n\tExample: AlphabatizeSolution.py <solution name> [<output solution name>]')
        sys.exit(2)
    else:
        input_name = sys.argv[1]
        if len(sys.argv) > 2:
            output_name = sys.argv[2]
        else:
            file_name, extension = os.path.splitext(input_name)
            output_name = file_name + '.tmp' + extension
    
    solution = None
    with open(input_name) as input_file:
        solution = Solution(input_file.read())
        
    with open(output_name, 'w') as output_file:
        output_file.write(str(solution))
        