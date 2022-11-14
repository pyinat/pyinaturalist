"""Utilities for copying and modifying docstrings with type annotations"""
import re
from inspect import cleandoc
from typing import Callable, Dict, Iterable, List, Optional, get_type_hints

from pyinaturalist.constants import TemplateFunction

SECTION_PATTERN = re.compile(r'\s*\w+:$')
DEFAULT_SECTIONS = ['Description', 'Args', 'Example', 'Returns', 'Raises']


class ApiDocstring:
    """Class representing a docstring for an API request function.
    This helps with doc reuse by splitting up the docstring into extensible sections.
    Assumes Google-style docstrings.
    """

    def __init__(self, docstring: Optional[str] = None):
        self.sections = self._split_sections(docstring or '')

    def extend(
        self,
        docstring: str,
        include_sections: Optional[List[str]] = None,
        exclude_args: Optional[Iterable[str]] = None,
    ):
        """Extend with contents from another docstring

        Args:
            docstring: Docstring to extend this one with
            include_sections: Sections to include; if not specified, all sections will be included
            exclude: Arguments to exclude from the new docstring
        """
        new_sections = self._split_sections(docstring)
        include_sections = include_sections or list(new_sections.keys())

        # Extend args
        args_section = self._exclude_args(new_sections.pop('Args', ''), exclude_args)
        if args_section and 'Args' in include_sections:
            if self.sections['Args']:
                args_section = f'\n{args_section}'
            self.sections['Args'] += args_section

        # Add other sections if they don't already exist
        for section, content in new_sections.items():
            if section in include_sections and not self.sections.get(section):
                self.sections[section] = content

    # Note: Currently this only applies to single-line arg docs; no need for multi-line (yet)
    @staticmethod
    def _exclude_args(args_section: str, exclude_args: Optional[Iterable[str]] = None) -> str:
        if not exclude_args:
            return args_section

        def is_excluded(line):
            return any(line.strip().startswith(f'{arg}:') for arg in exclude_args)

        arg_lines = [line for line in args_section.splitlines() if not is_excluded(line)]
        return '\n'.join(arg_lines)

    @staticmethod
    def _indent(value: str, level: int = 1) -> str:
        prefix = ' ' * 4 * level
        return prefix + value.replace('\n', f'\n{prefix}')

    @staticmethod
    def _split_sections(docstring: str) -> Dict[str, str]:
        """Split a docstring into a dict of ``{section_title: section_content}``"""
        docstring = docstring or ''
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

    def __str__(self) -> str:
        """Reassemble sections back into a complete docstring"""
        docstring = self.sections['Description'] + '\n\n'
        for section, content in self.sections.items():
            if content and section != 'Description':
                docstring += f'{section}:\n{self._indent(content)}\n\n'
        return docstring


def copy_annotations(
    target_function: Callable,
    template_functions: List[TemplateFunction],
    include_return: bool = True,
) -> Callable:
    """Copy type annotations from one or more template functions to a target function"""
    for template_function in template_functions:
        annotations = get_type_hints(template_function)
        if not include_return:
            annotations.pop('return', None)
        if hasattr(target_function, '__annotations__'):
            for k, v in annotations.items():
                target_function.__annotations__[k] = v

    return target_function


def copy_docstrings(
    target_function: Callable,
    template_functions: List[TemplateFunction],
    include_sections: Optional[List[str]] = None,
    exclude_args: Optional[Iterable[str]] = None,
) -> Callable:
    """Copy docstrings from one or more template functions to a target function.
    Assumes Google-style docstrings.

    Args:
        target_function: Function to modify
        template_functions: Functions containing docstrings to apply to ``target_function``
        include: Sections to include; if not specified, all sections will be included
        exclude_args: Arguments to exclude from the new docstring
    """
    doc = ApiDocstring(target_function.__doc__)
    for template_function in template_functions:
        doc.extend(template_function.__doc__, include_sections, exclude_args)

    target_function.__doc__ = str(doc)
    return target_function
