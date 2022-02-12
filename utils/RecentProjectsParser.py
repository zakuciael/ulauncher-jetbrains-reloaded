""" Contains parser for JetBrains IDEs "Recent projects" files """

import glob
import os
from collections import OrderedDict
from typing import Optional, cast, List
from xml.etree import ElementTree

from data.IdeKey import IdeKey
from data.IdeProject import IdeProject

TIMESTAMP_XML_PATH = 'value/RecentProjectMetaInfo/option[@name="projectOpenTimestamp"]'
RECENT_PROJECTS_MANAGER_PATH = './/component[@name="RecentProjectsManager"][1]'
RECENT_DIRECTORY_PROJECTS_MANAGER_PATH = \
    './/component[@name="RecentDirectoryProjectsManager"][1]'


# pylint: disable=too-few-public-methods
class RecentProjectsParser:
    """ Parser for JetBrains IDEs "Recent projects" files """

    @staticmethod
    def parse(file_path: str, ide_key: IdeKey) -> List[IdeProject]:
        """
        Parses the "Recent projects" file
        :param file_path: The path to the file
        :param ide_key: IDE key identified with the file
        :return: Parsed projects
        """

        if not os.path.isfile(file_path):
            return []

        root = ElementTree.parse(file_path).getroot()

        raw_projects = \
            root.findall(
                f'{RECENT_PROJECTS_MANAGER_PATH}/option[@name="recentPaths"]/list/option'
            ) + \
            root.findall(
                f'{RECENT_DIRECTORY_PROJECTS_MANAGER_PATH}/option[@name="recentPaths"]/list/option'
            ) + \
            root.findall(
                f'{RECENT_PROJECTS_MANAGER_PATH}/option[@name="additionalInfo"]/map/entry'
            ) + \
            root.findall(
                f'{RECENT_DIRECTORY_PROJECTS_MANAGER_PATH}/option[@name="additionalInfo"]/map/entry'
            ) + \
            root.findall(
                f'{RECENT_PROJECTS_MANAGER_PATH}/option[@name="groups"]/list/ProjectGroup/' +
                'option[@name="projects"]/list/option'
            )
        project_paths = list(OrderedDict.fromkeys([
            (project.attrib['value' if 'value' in project.attrib else 'key']).replace(
                "$USER_HOME$", "~"
            ) for project in raw_projects
        ]))

        output = []
        for path in project_paths:
            full_path = os.path.expanduser(path)
            name_file = full_path + '/.idea/.name'
            name = ''

            if os.path.exists(name_file):
                with open(name_file, 'r', encoding="utf8") as file:
                    name = file.read().replace('\n', '')

            icons = glob.glob(os.path.join(full_path, '.idea', 'icon.*'))

            output.append(IdeProject(
                name=name or os.path.basename(path),
                path=path,
                icon=cast(Optional[str], icons[0] if len(icons) > 0 else None),
                score=0,
                ide=ide_key
            ))

        return output
