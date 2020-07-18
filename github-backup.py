#!/usr/bin/env python3
# vim: awa:sts=4:ts=4:sw=4:et:cin:fdm=manual:tw=120:ft=python

from ansimarkup import AnsiMarkup, parse
from app_settings import app_settings
import argparse
import datetime
import json
import os
from pathlib import Path
import requests
import shlex
import shutil
import subprocess
import sys
import tarfile
import traceback

user_tags = {
    'info'        : parse('<bold><green>'),    # bold green
    'error'       : parse('<bold><red>'),      # bold red
    'mail'        : parse('<blink><red>'),     # bliink red
    'label'       : parse('<bold><cyan>'),     # bold cyan
    'value'       : parse('<reset>'),          # white
    'sysinfo'     : parse('<bold><yellow>'),   # bold yellow
    'quote'       : parse('<bold><cyan>'),     # bold cyan
    'location'    : parse('<bold><cyan>'),     # bold cyan
    'weather'     : parse('<reset>'),          # white
    'greeting'    : parse('<bold><green>'),    # bold green
    'loginout'    : parse('<bold><green>'),    # bold green
    'apt'         : parse('<bold><yellow>'),   # bold yellow
    'reboot'      : parse('<bold><red>'),      # bold red
}

am = AnsiMarkup(tags=user_tags)

_TIME_OUT = 5.0
_GIT_CLONE_CMD = 'git clone --quiet --mirror'
"${GHBU_GIT_CLONE_CMD}${GHBU_ORG}/${REPO}.git ${GHBU_BACKUP_DIR}/${GHBU_ORG}-${REPO}-${TSTAMP}.git && tgz ${GHBU_BACKUP_DIR}/${GHBU_ORG}-${REPO}-${TSTAMP}.git &>/dev/null"
"${GHBU_GIT_CLONE_CMD}${GHBU_ORG}/${REPO}.wiki.git ${GHBU_BACKUP_DIR}/${GHBU_ORG}-${REPO}.wiki-${TSTAMP}.git 2>/dev/null && tgz ${GHBU_BACKUP_DIR}/${GHBU_ORG}-${REPO}.wiki-${TSTAMP}.git &>/dev/null"

#Backing up jasonivey/settings
#Info:: git clone --quiet --mirror git@github.com:jasonivey/settings.git /Users/jasoni/tmp/github-backups/jasonivey-settings-20200710-0024.git && tgz /Users/jasoni/tmp/github-backups/jasonivey-settings-20200710-0024.git
#Backing up jasonivey/settings.wiki (if any)
#Backing up jasonivey/settings issues
#Info:: curl --silent https://api.github.com/repos/jasonivey/settings/issues -q > /Users/jasoni/tmp/github-backups/jasonivey-settings.issues-20200710-0024 && tgz /Users/jasoni/tmp/github-backups/jasonivey-settings.issues-20200710-0024
#Backing up jasonivey/scripts
#Info:: git clone --quiet --mirror git@github.com:jasonivey/scripts.git /Users/jasoni/tmp/github-backups/jasonivey-scripts-20200710-0024.git && tgz /Users/jasoni/tmp/github-backups/jasonivey-scripts-20200710-0024.git
#Backing up jasonivey/scripts.wiki (if any)
#Info:: git clone --quiet --mirror git@github.com:jasonivey/scripts.wiki.git /Users/jasoni/tmp/github-backups/jasonivey-scripts.wiki-20200710-0024.git 2>/dev/null && tgz /Users/jasoni/tmp/github-backups/jasonivey-scripts.wiki-20200710-0024.git
#Backing up jasonivey/scripts issues
#Info:: curl --silent https://api.github.com/repos/jasonivey/scripts/issues -q > /Users/jasoni/tmp/github-backups/jasonivey-scripts.issues-20200710-0024 && tgz /Users/jasoni/tmp/github-backups/jasonivey-scripts.issues-20200710-0024

class RepositoryInfo:
    def __init__(self, info):
        self._parse_info(info)

    def _parse_info(self, info):
        self._name = info['name']
        self._git_url = info['git_url']
        has_issues = info['has_issues'] if 'has_issues' in info.keys() else False
        app_settings.lowinfo(f'{self._name} has issues: {has_issues}')
        self._issues_url = info['issues_url'] if has_issues and 'issues_url' in info.keys() else False
        if self._issues_url:
            index = self._issues_url.find('{')
            self._issues_url = self._issues_url[:index] if index != -1 else self._issues_url
        has_wiki = info['has_wiki'] if 'has_wiki' in info.keys() else False
        app_settings.lowinfo(f'{self._name} has wiki: {has_wiki}')
        self._wiki_url = info['wiki_url'] if has_wiki and 'wiki_url' in info.keys() else None
        if self._wiki_url is None and has_wiki:
            index = self._git_url.rfind('.git')
            self._wiki_url = f'{self._git_url[:index]}.wiki.git' if index != -1 else None

    @property
    def name(self):
        return self._name

    @property
    def git_url(self):
        return self._git_url

    @property
    def issues_url(self):
        return self._issues_url

    @property
    def wiki_url(self):
        return self._wiki_url

    def __str__(self):
        s = f'\n  name:           {self.name}'
        s += f'\n  git repository: {self.git_url}'
        if self.issues_url: s += f'\n  issues url:     {self.issues_url}'
        if self.wiki_url: s += f'\n  wiki url:       {self.wiki_url}'
        return s

def _parse_args():
    parser = argparse.ArgumentParser(description='Backup Github repositories')
    parser.add_argument('-v', '--verbose', action='count', default=0, help='increase output verbosity')
    parser.add_argument('-u', '--username', required=True, default='jasonivey', help='username of the Github account to backup')
    parser.add_argument('-d', '--destination', required=True, default='/tmp/github-backups', help='destination directory for Github backups')
    parser.add_argument('repositories', metavar='repository', nargs='*', action='append', help='specify which repositories to backup')
    args = parser.parse_args()
    app_settings.update(vars(args))
    app_settings.print_settings(print_always=False)

def _get_timezone_info():
    return datetime.datetime.now(datetime.timezone.utc).astimezone().tzinfo

def _get_now():
    return datetime.datetime.now(_get_timezone_info())

def _get_backup_timestamp():
    return f'{_get_now():%Y%m%d-%H%M}'

def _call_external_process(command, ignore_errors=False):
    args = shlex.split(command)
    try:
        app_settings.info(f'executing \'{command}\'')
        #subprocess.run(args, check=True, encoding='utf-8', shell=True, env=os.environ, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(args, check=True, encoding='utf-8', stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except subprocess.SubprocessError as err:
        if ignore_errors:
            app_settings.info(f'\'{command}\' returned: {err}')
            return True
        else:
            app_settings.error(f'\'{command}\' returned: {err}')
            return False
    except Exception as err:
        if ignore_errors:
            app_settings.info(f'\'{command}\' returned: {err}')
            return True
        else:
            app_settings.error(f'\'{command}\' returned: {err}')
            return False

def _call_uri(uri):
    try:
        app_settings.info(f'calling {uri} with a {_TIME_OUT} second timeout')
        response = requests.get(uri, timeout=_TIME_OUT)
        response.raise_for_status()
        response_str = response.text.strip()
        return None if not response_str else response_str
    except requests.exceptions.RequestException as e:
        app_settings.error(f'error while calling {uri}')
        app_settings.error(str(e))
        return None

def _get_user_repository_info(username, repository):
    app_settings.info(f'quering for user ({username}) repository ({repository}) information')
    uri = f'https://api.github.com/repos/{username}/{repository}'
    response_str = _call_uri(uri)
    if not response_str:
        app_settings.error(f'while trying to query {repository} under {username} account')
        return None
    repository_json = json.loads(response_str)
    return RepositoryInfo(repository_json)

def _get_user_repository_infos(username):
    app_settings.info(f'quering for user ({username}) repositories information')
    uri = f'https://api.github.com/users/{username}/repos'
    response_str = _call_uri(uri)
    if not response_str:
        app_settings.error(f'while trying to query {repository} under {username} account')
        return None
    repositories_json = json.loads(response_str)
    repository_infos = []
    for repository_json in repositories_json:
        repository_infos.append(RepositoryInfo(repository_json))
        app_settings.info(f'found repository {repository_infos[-1].name} at {repository_infos[-1].git_url}')
    return repository_infos

def _remove_filesystem_object(fs_path):
    if fs_path.exists():
        if fs_path.is_file():
            os.remove(fs_path)
        else:
            shutil.rmtree(fs_path, ignore_errors=True)

def _archive_and_compress(tar_path, backup_path):
    try:
        _remove_filesystem_object(tar_path)
        with tarfile.open(tar_path, 'w:bz2') as tar:
            tar.add(backup_path)
        app_settings.info(f'successfully created and populated bz2 tar file {tar_path}')
        return True
    except tarfile.TarError as err:
        app_settings.error(f'creating or populating {tar_path} with {backup_path}: {err}')
        return False
    except Exception as err:
        app_settings.error(f'creating or populating {tar_path} with {backup_path}: {err}')
        return False

def github_backup_git_repository(repository, username, dest_dir_path, timestamp):
    app_settings.info(f'backing up git repository {repository.name} {repository.git_url}')
    repo_backup_path = dest_dir_path.joinpath(f'{username}-{repository.name}-{timestamp}.git')
    repo_backup_tar_file = dest_dir_path.joinpath(f'{username}-{repository.name}-{timestamp}.git.tar.bz2')
    command = f'git clone --quiet --mirror {repository.git_url} {repo_backup_path}'
    app_settings.info(f'calling {command}')
    result = _call_external_process(command)
    if result:
        result = _archive_and_compress(repo_backup_tar_file, repo_backup_path)
    _remove_filesystem_object(repo_backup_path)
    return result

def github_backup_git_wiki(repository, username, dest_dir_path, timestamp):
    app_settings.info(f'backing up git wiki {repository.name} {repository.git_url}')
    if not repository.wiki_url:
        app_settings.info(f'no git wiki found {repository.name} {repository.git_url}')
        return True
    wiki_backup_path = dest_dir_path.joinpath(f'{username}-{repository.name}-{timestamp}.wiki.git')
    wiki_backup_tar_file = dest_dir_path.joinpath(f'{username}-{repository.name}-{timestamp}.wiki.git.tar.bz2')
    command = f'git clone --quiet --mirror {repository.wiki_url} {wiki_backup_path}'
    result = _call_external_process(command, ignore_errors=True)
    if result and wiki_backup_path.exists():
        result = _archive_and_compress(wiki_backup_tar_file, wiki_backup_path)
    _remove_filesystem_object(wiki_backup_path)
    return result

def github_backup_git_issues(repository, username, dest_dir_path, timestamp):
    app_settings.info(f'backing up git issues {repository.name} {repository.git_url}')
    if not repository.issues_url:
        app_settings.info(f'no git issues found {repository.name} {repository.git_url}')
        return True
    issues_backup_path = dest_dir_path.joinpath(f'{username}-{repository.name}-{timestamp}.issues.git')
    issues_backup_tar_file = dest_dir_path.joinpath(f'{username}-{repository.name}-{timestamp}.issues.git.tar.bz2')
    command = f'http -b {repository.issues_url} --output {issues_backup_path}'
    result = _call_external_process(command)
    if result:
        result = _archive_and_compress(issues_backup_tar_file, issues_backup_path)
    _remove_filesystem_object(issues_backup_path)
    return result

def github_backup_repository(repository, username, dest_dir_path):
    timestamp = _get_backup_timestamp()
    if not github_backup_git_repository(repository , username, dest_dir_path, timestamp):
        app_settings.error(f'backing up github repository {repository.git_url}')
        return False
    if not github_backup_git_wiki(repository, username, dest_dir_path, timestamp):
        app_settings.error(f'backing up github wiki repository {repository.wiki_url}')
        return False
    if not github_backup_git_issues(repository, username, dest_dir_path, timestamp):
        app_settings.error(f'backing up github issues repository {repository.issues_url}')
        return False
    app_settings.info(f'successfully backed up {username} github repository {repository.git_url}')
    return True

def github_backup_reposities(repositories, username, dest_dir_path):
    app_settings.info('backing up repositores...')
    for repository in repositories:
        app_settings.info(f'backing up github repository {repository.name} for {username}')
        if not github_backup_repository(repository, username, dest_dir_path):
            app_settings.error(f'quitting backup process due to error while backing up {repository.name}')
            return False
    return True

def main():
    _parse_args()
    try:
        repository_names = app_settings.repositories
        repository_infos = []
        if not repository_names:
            repository_infos = _get_user_repository_infos(app_settings.username)
        else:
            for repository_name in repository_names:
                repository_info = _get_user_repository_info(app_settings.username, repository_name)
                if repository_info:
                    repository_infos.append(repository_info)
        if repository_infos:
            dest_dir_path = Path(app_settings.destination).resolve()
            dest_dir_path.mkdir(parents=True, exist_ok=True)
            github_backup_reposities(repository_infos, app_settings.username, dest_dir_path)
        else:
            app_settings.error('there are no repositories to backup')
            return 1
    except:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stderr)
        return 1
    return 0

if __name__ == '__main__':
    sys.exit(main())
