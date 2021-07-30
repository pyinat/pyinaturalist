"""Utilities for copying and modifying docstrings, mainly for API request functions"""
import re
from inspect import cleandoc
from typing import Callable, Dict, List, get_type_hints

from pyinaturalist.constants import TemplateFunction

SECTION_PATTERN = re.compile(r'\s*\w+:$')
DEFAULT_SECTIONS = ['Description', 'Args', 'Example', 'Returns', 'Raises']


def copy_annotations(
    target_function: Callable, template_functions: List[TemplateFunction], include_return: bool = True
) -> Callable:
    """Copy type annotations from one or more template functions to a target function"""
    for template_function in template_functions:
        annotations = get_type_hints(template_function)
        if not include_return:
            annotations.pop('return', None)
        for k, v in annotations.items():
            target_function.__annotations__[k] = v

    return target_function


def copy_docstrings(
    target_function: Callable, template_functions: List[TemplateFunction], include: List[str] = None
) -> Callable:
    """Copy docstrings from one or more template functions to a target function.
    Assumes Google-style docstrings.

    Args:
        target_function: Function to modify
        template_functions: Functions containing docstrings to apply to ``target_function``
        include: Sections to include; if not specified, all sections will be included
    """
    docstring = ApiDocstring(target_function.__doc__)
    for template_function in template_functions:
        docstring.extend(template_function.__doc__, include=include)

    target_function.__doc__ = str(docstring)
    return target_function


class ApiDocstring:
    """Class representing a docstring for an API request function.
    This helps with doc reuse by splitting up the docstring into extensible sections.
    Assumes Google-style docstrings.
    """

    def __init__(self, docstring: str = None):
        self.sections = self._split_sections(docstring or '')

    @staticmethod
    def _indent(value: str, level: int = 1) -> str:
        prefix = ' ' * 4 * level
        return prefix + value.replace('\n', f'\n{prefix}')

    @staticmethod
    def _split_sections(docstring: str) -> Dict[str, str]:
        """Split a docstring into a dict of ``{section_title: section_content}``"""
        sections = {k: '' for k in DEFAULT_SECTIONS}
        current_section = 'Description'

        for line in docstring.splitlines():
            if SECTION_PATTERN.match(line):
                current_section = line.strip().rstrip(':')
                sections[current_section] = ''
            else:
                sections[current_section] += line + '\n'

        # Unindent section content and trim trailing whitespace
        return {k: cleandoc(v.rstrip()) for k, v in sections.items()}

    def extend(self, docstring: str, include: List[str] = None):
        """Extend with contents from another docstring

        Args:
            docstring: Docstring to extend this one with
            include: Sections to include; if not specified, all sections will be included
        """
        new_sections = self._split_sections(docstring)
        include = include or list(new_sections.keys())

        # Extend args
        args = new_sections.pop('Args', '')
        if args and 'Args' in include:
            if self.sections['Args']:
                args = f'\n{args}'
            self.sections['Args'] += args

        # Add other sections if they don't already exist
        for section, content in new_sections.items():
            if section in include and not self.sections.get(section):
                self.sections[section] = content

    def __str__(self) -> str:
        """Reassemble sections back into a complete docstring"""
        docstring = self.sections['Description'] + '\n\n'
        for section, content in self.sections.items():
            if content and section != 'Description':
                docstring += f'{section}:\n{self._indent(content)}\n\n'
        return docstring
