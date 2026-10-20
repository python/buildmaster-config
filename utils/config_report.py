import argparse
import os
import re
import shlex
import shutil
import sys
import textwrap
from collections.abc import Mapping
from pathlib import Path


_COLOR = sys.stdout.isatty() and 'NO_COLOR' not in os.environ
_WIDTH = shutil.get_terminal_size(fallback=(100, 24)).columns
_STYLES = {'bold': 1, 'cyan': 36, 'dim': 2}


def style(text, name):
    if not _COLOR:
        return text
    return f'\033[{_STYLES[name]}m{text}\033[0m'


def format_value(value):
    # Handle things that look like renderers to avoid memory addresses in output
    if hasattr(value, 'fn'):
        name = getattr(value.fn, '__qualname__', type(value.fn).__qualname__)
        if value.args or value.kwargs:
            return f'renderer({name}, args={value.args!r}, kwargs={value.kwargs!r})'
        return f'renderer({name})'
    return str(value)


def print_value(label, value, indent):
    prefix = (' ' * indent + str(label)).ljust(indent + 12) + '  '
    available_width = max(20, _WIDTH - len(prefix))
    text = format_value(value)

    lines = []
    for paragraph in text.splitlines() or ['']:
        wrapped = textwrap.wrap(
            paragraph,
            width=available_width,
            break_long_words=False,
            break_on_hyphens=False,
        )
        lines.extend(wrapped or [''])

    print(style(prefix, 'cyan') + lines[0])
    for line in lines[1:]:
        print(' ' * len(prefix) + line)


def print_detail(label, value, indent=2):
    heading = ' ' * indent + str(label)

    if isinstance(value, Mapping) and value:
        print(style(heading, 'cyan'))
        for key, item in value.items():
            print_detail(key, item, indent + 2)
        return

    if isinstance(value, (list, tuple)) and value:
        if label == 'command':
            command = shlex.join(format_value(argument) for argument in value)
            print_value(label, command, indent)
        elif all(isinstance(item, str) for item in value):
            print_value(label, ', '.join(value), indent)
        else:
            print(style(heading, 'cyan'))
            for item in value:
                print_detail('-', item, indent + 2)
        return

    print_value(label, value, indent)


def report(config):
    parser = argparse.ArgumentParser(description='List configured builders.')
    parser.add_argument(
        '-v', '--verbose', action='count', default=0,
        help='show builder details; repeat to include build steps',
    )
    parser.add_argument(
        '-f', '--filter',
        help='Only report builders with a matching name',
    )
    args = parser.parse_args()

    for builder in sorted(config['builders'], key=lambda b: b.name):
        if not re.search(args.filter or '.*', builder.name, flags=re.IGNORECASE):
            continue
        print(style(builder.name, 'bold'))
        if not args.verbose:
            continue
        print_detail('Factory', type(builder.factory).__name__)
        for key in (
            'workernames',
            'builddir',
            'tags',
            'env',
            'properties',
            'defaultProperties',
            'description',
        ):
            value = getattr(builder, key)
            if not value:
                continue
            if isinstance(value, list):
                value = sorted(value)
            print_detail(key, value)
        if args.verbose > 1:
            for step in builder.factory.steps:
                print(f'    {step.step_class.__name__}')
                if step.args:
                    print_detail('args', step.args, indent=6)
                # Show useful inherited defaults as well as explicit overrides.
                details = {}
                if args.verbose > 2:
                    for key in (
                        'command', 'env', 'timeout', 'maxTime',
                        'haltOnFailure', 'flunkOnFailure', 'warnOnFailure',
                        'alwaysRun',
                    ):
                        value = getattr(step.step_class, key, None)
                        if value is not None:
                            details[key] = value
                details.update(step.kwargs)
                for key, value in details.items():
                    print_detail(key, value, indent=6)
        print()

    counts = [
        f'{len(config[key])} {key}'
        for key in ('builders', 'workers', 'schedulers')
    ]
    totals = 'Totals: ' + ' · '.join(counts)
    print(style(totals, 'dim'))


if __name__ == '__main__':
    import runpy

    root_dir = Path(__file__) / '..' / '..'
    master_config = root_dir / 'master' / 'master.cfg'

    report(runpy.run_path(master_config.resolve())['BuildmasterConfig'])
