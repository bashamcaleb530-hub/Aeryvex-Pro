#!/bin/sh
# Local, non-destructive setup. No sudo, package manager, network, or downloads.
# Verified host: Debian GNU/Linux 13.6 (trixie), Python 3.12.14, Godot 4.2.2.
set -eu
factory_script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
if ! command -v python3 >/dev/null 2>&1; then
    printf '%s\n' 'BLOCKED: Python 3.10+ is required. Install Python using your system administrator/package manager, then rerun.' >&2
    exit 1
fi
exec python3 - "$factory_script_dir" "$@" <<'PY'
import argparse
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import sys

parser = argparse.ArgumentParser(description='Install a local Aeryvex factory UI launcher without modifying system packages or existing projects.')
parser.add_argument('--prefix', type=Path, default=Path(os.environ.get('XDG_DATA_HOME', str(Path.home() / '.local/share'))) / 'aeryvex-game-factory')
parser.add_argument('--check', action='store_true', help='Only report local dependencies; create nothing')
arguments = parser.parse_args(sys.argv[2:])
if sys.version_info < (3, 10):
    sys.exit('BLOCKED: Python 3.10+ required; found ' + sys.version.split()[0])
print('Python:', sys.version.split()[0], '(standard library only; no pip dependencies)')
engine = os.environ.get('GODOT_BIN') or shutil.which('godot4') or shutil.which('godot')
engine_ready = False
if engine:
    try:
        result = subprocess.run([engine, '--version'], capture_output=True, text=True, timeout=15)
        output = result.stdout + result.stderr
        match = re.match(r'^(\d+)\.(\d+)(?:\.(\d+))?\.([A-Za-z]+)(?:\.|\s|$)', output.strip())
        engine_ready = result.returncode == 0 and bool(match) and (int(match[1]), int(match[2])) >= (4, 2) and not re.search(r'(?im)^\s*(?:SCRIPT ERROR:|ERROR:|Parse Error:)', output)
        print('Godot:', output.strip())
    except (OSError, subprocess.TimeoutExpired) as error:
        print('BLOCKED Godot dependency:', error)
if not engine_ready:
    print('BLOCKED game QA/export: provide Godot 4.2+ locally and set GODOT_BIN; the UI itself needs only Python.')
else:
    version = f'{match[1]}.{match[2]}' + (f'.{match[3]}' if match[3] else '') + '.' + match[4]
    configured = os.environ.get('FACTORY_EXPORT_TEMPLATES')
    template_root = Path(configured).expanduser() if configured else Path(os.environ.get('XDG_DATA_HOME', str(Path.home() / '.local/share'))) / 'godot/export_templates'
    candidates = [template_root, template_root / version] if configured else [template_root / version]
    found = False
    for directory in candidates:
        try:
            found = (directory / 'version.txt').read_text().strip() == version and all((directory / name).is_file() and (directory / name).stat().st_size > 0 for name in ['linux_release.x86_64', 'linux_debug.x86_64'])
        except OSError:
            continue
        if found:
            print('Linux export templates:', directory)
            break
    if not found:
        print('BLOCKED native export: matching official ' + version + ' templates required (version.txt, linux_release.x86_64, linux_debug.x86_64); set FACTORY_EXPORT_TEMPLATES to their directory. No download performed.')
if arguments.check:
    print('Dependency check complete; nothing installed.')
    sys.exit(0)
prefix = arguments.prefix.expanduser().absolute()
if prefix.exists() or prefix.is_symlink():
    sys.exit('Refusing to overwrite existing installation: ' + str(prefix) + '. Choose an empty new --prefix; preserve existing projects separately.')
source = Path(sys.argv[1]).resolve().parents[0]
application = prefix / 'app'
try:
    shutil.copytree(source, application / 'ai_factory', ignore=shutil.ignore_patterns('__pycache__', '*.pyc', 'verification', 'tests', 'plans'))
    binary_directory = prefix / 'bin'
    binary_directory.mkdir()
    launcher = binary_directory / 'aeryvex-factory'
    python = shlex.quote(sys.executable)
    module_path = shlex.quote(str(application))
    workspace = shlex.quote(str(prefix / 'projects'))
    launcher.write_text('#!/bin/sh\nset -eu\nexport PYTHONPATH=' + module_path + '\nexec ' + python + ' -m ai_factory --workspace ' + workspace + ' ui "$@"\n')
    launcher.chmod(0o755)
except OSError as error:
    sys.exit('Setup interrupted; preserve/inspect partial installation at ' + str(prefix) + ': ' + str(error))
print('Installed locally:', prefix)
print('Launch UI:', shlex.quote(str(launcher)) + ' --port 8765')
print('Direct launch: PYTHONPATH=' + module_path + ' ' + python + ' -m ai_factory --workspace ' + workspace + ' ui --port 8765')
print('Open http://127.0.0.1:8765 after launching. No system packages or existing projects were changed.')
PY
