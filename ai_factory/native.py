"""Real Linux exports from an immutable, runtime-checked source snapshot.

Templates are supplied by the user from the matching official Godot distribution.
This module never installs software, downloads templates, or edits godot/.
"""
import json
import os
import platform
import re
import shutil
import subprocess
import tempfile
import uuid
import zipfile
from pathlib import Path
from . import core

_ERROR = re.compile(r'(?im)^\s*(?:SCRIPT ERROR:|ERROR:|Parse Error:)')
_PRESET = '''[preset.0]
name="Linux"
platform="Linux/X11"
runnable=true
export_filter="all_resources"
include_filter="*.json"
exclude_filter=""
export_path=""
script_export_mode=1

[preset.0.options]
custom_template/debug={debug}
custom_template/release={release}
binary_format/architecture="x86_64"
binary_format/embed_pck=false
texture_format/bptc=true
texture_format/s3tc=true
texture_format/etc=false
texture_format/etc2=false
'''


class _Blocked(Exception):
    pass


class _Failed(Exception):
    pass


def _templates(version):
    configured = os.environ.get('FACTORY_EXPORT_TEMPLATES')
    root = Path(configured).expanduser() if configured else Path(os.environ.get('XDG_DATA_HOME', str(Path.home() / '.local/share'))) / 'godot/export_templates'
    candidates = [root, root / version] if configured else [root / version]
    directory = next((p.resolve() for p in candidates if (p / 'version.txt').is_file()), candidates[-1].resolve())
    requirement = ('Matching official Godot ' + version + ' Linux export templates required: version.txt, '
                   'linux_release.x86_64 and linux_debug.x86_64. Set FACTORY_EXPORT_TEMPLATES to that '
                   'version directory (or its parent), or install them under '
                   '$XDG_DATA_HOME/godot/export_templates/' + version + '. Checked ' + str(directory))
    if not directory.is_dir():
        raise _Blocked(requirement)
    version_file = directory / 'version.txt'
    if not version_file.is_file() or version_file.read_text().strip() != version:
        raise _Blocked(requirement + '; version.txt must contain exactly ' + version)
    for name in ['linux_release.x86_64', 'linux_debug.x86_64']:
        template = directory / name
        if not template.is_file() or template.stat().st_size == 0:
            raise _Blocked(requirement + '; missing or empty ' + name)
    return directory


def _run(name, command, env, cwd, logs, checks, marker=None):
    output = ''
    exit_code = None
    try:
        result = subprocess.run(command, env=env, cwd=cwd, capture_output=True, text=True, errors='replace', timeout=120)
        output = result.stdout + result.stderr
        exit_code = result.returncode
        passed = exit_code == 0 and not _ERROR.search(output)
        if marker:
            passed = passed and marker in output.splitlines()
    except subprocess.TimeoutExpired as error:
        output = 'Timed out after 120 seconds\n'
        for value in (error.stdout, error.stderr):
            if value:
                output += value.decode(errors='replace') if isinstance(value, bytes) else value
        passed = False
    except OSError as error:
        output = str(error)
        passed = False
    log = logs / (name + '.log')
    log.write_text(output)
    checks.append({'name': name, 'command': command, 'cwd': str(cwd), 'exit_code': exit_code,
                   'passed': bool(passed), 'log': str(log), 'log_sha256': core.digest(log)})
    if not passed:
        raise _Failed(name + ' failed; inspect ' + str(log))
    return output


def export_linux(path):
    """Return/persist native.json with BLOCKED, FAILED, or NATIVE_CHECKED status.

    NATIVE_CHECKED means a Linux x86_64 executable and PCK passed relocated
    headless startup and the packaged gameplay scenario. GUI/hardware review is
    still pending. Successful artifacts are in dist/linux/<run id>/; logs are
    outside managed game sources in .native/<run id>/logs/.
    """
    path = Path(path).resolve()
    run_id = uuid.uuid4().hex
    report = {'status': 'BLOCKED', 'target': 'linux-x86_64', 'checks': [],
              'visual_review': 'PENDING', 'hardware_review': 'PENDING'}
    try:
        game = path / 'godot'
        if game.is_symlink() or any(p.is_symlink() for p in game.rglob('*')):
            raise _Blocked('Source symlinks are forbidden for native export; preserve and resolve them before QA.')
        for target in [path / '.native', path / 'dist', path / 'dist/linux', path / 'native.json', path / 'native.tmp']:
            if target.is_symlink():
                raise _Blocked('Native output symlink is forbidden: ' + str(target))
        if core.status(path)['qa'] != 'RUNTIME_CHECKED':
            raise _Blocked('Current source and revision require evidence-bound RUNTIME_CHECKED QA; build and test before native export.')
        evidence = core.evidence_key(path)
        campaign_enabled = bool(core.load(path)['config'].get('campaign'))
        report['evidence'] = evidence
        if platform.system() != 'Linux' or platform.machine().lower() not in ('x86_64', 'amd64'):
            raise _Blocked('Linux x86_64 host required to run the relocated Linux executable smoke test.')
        engine = os.environ.get('GODOT_BIN') or shutil.which('godot4') or shutil.which('godot')
        if not engine:
            raise _Blocked('Godot 4.2+ unavailable; set GODOT_BIN to a local Godot executable.')
        resolved_engine = shutil.which(engine)
        if not resolved_engine:
            raise _Blocked('Godot executable unavailable: ' + engine + '; set GODOT_BIN to a local Godot 4.2+ executable.')
        engine = str(Path(resolved_engine).resolve())
        logs = path / '.native' / run_id / 'logs'
        logs.mkdir(parents=True)
        report['logs'] = str(logs)
        with tempfile.TemporaryDirectory(prefix='factory-native-') as temporary:
            work = Path(temporary)
            env = os.environ.copy()
            for key, suffix in [('XDG_DATA_HOME', 'data'), ('XDG_CONFIG_HOME', 'config'), ('XDG_CACHE_HOME', 'cache')]:
                directory = work / suffix
                directory.mkdir()
                env[key] = str(directory)
            version_output = _run('version', [engine, '--version'], env, work, logs, report['checks'])
            match = re.match(r'^(\d+)\.(\d+)(?:\.(\d+))?\.([A-Za-z]+)(?:\.|\s|$)', version_output.strip())
            if not match or (int(match[1]), int(match[2])) < (4, 2):
                raise _Blocked('Godot 4.2+ required; engine reported ' + version_output.strip())
            # Export template directory convention excludes the official/build hash suffix.
            version = f'{match[1]}.{match[2]}' + (f'.{match[3]}' if match[3] else '') + '.' + match[4]
            report['engine_version'] = version_output.strip()
            templates = _templates(version)
            report['templates'] = str(templates)
            report['template_sha256'] = {name: core.digest(templates / name) for name in ['version.txt', 'linux_release.x86_64', 'linux_debug.x86_64']}
            source = work / 'source'
            shutil.copytree(game, source, ignore=shutil.ignore_patterns('.godot'))
            (source / 'export_presets.cfg').write_text(_PRESET.format(
                debug=json.dumps(str(templates / 'linux_debug.x86_64')),
                release=json.dumps(str(templates / 'linux_release.x86_64'))))
            _run('import', [engine, '--headless', '--editor', '--path', str(source), '--import'], env, work, logs, report['checks'])
            output = work / 'output'
            output.mkdir()
            executable = output / 'game.x86_64'
            _run('export', [engine, '--headless', '--path', str(source), '--export-release', 'Linux', str(executable)], env, work, logs, report['checks'])
            pack = executable.with_suffix('.pck')
            if not executable.is_file() or not pack.is_file() or not os.access(executable, os.X_OK) or not executable.stat().st_size or not pack.stat().st_size:
                raise _Failed('Godot export did not produce an executable game.x86_64 and nonempty game.pck.')
            # Unrelated temporary location, no project.godot/source files in cwd.
            with tempfile.TemporaryDirectory(prefix='factory-relocated-') as relocated_name:
                relocated = Path(relocated_name)
                for artifact in [executable, pack]:
                    shutil.copy2(artifact, relocated / artifact.name)
                for key in ['XDG_DATA_HOME', 'XDG_CONFIG_HOME', 'XDG_CACHE_HOME']:
                    env[key] = str(relocated / key.lower())
                    Path(env[key]).mkdir()
                binary = str(relocated / executable.name)
                _run('relocated_startup', [binary, '--headless', '--quit-after', '8'], env, relocated, logs, report['checks'])
                _run('relocated_scenario', [binary, '--headless', '--fixed-fps', '60', '--script', 'res://scenario.gd'], env, relocated, logs, report['checks'], marker='FACTORY_SCENARIO_PASS')
                if campaign_enabled:
                    scenario = [binary, '--headless', '--fixed-fps', '60', '--script', 'res://campaign_scenario.gd']
                    _run('relocated_campaign_scenario', scenario, env, relocated, logs, report['checks'], marker='FACTORY_CAMPAIGN_PASS')
                    # Separate executable process, same fresh user-data location:
                    # persistence must survive process teardown in the native pack.
                    _run('relocated_campaign_restart', scenario + ['--', '--verify-restart'], env, relocated, logs, report['checks'], marker='FACTORY_CAMPAIGN_RESTART_PASS')
                if (game / 'player_visual.json').is_file():
                    # The reviewed character must load and animate from the exported pack too.
                    _run('relocated_character_scenario', [binary, '--headless', '--fixed-fps', '60', '--script', 'res://character_scenario.gd'],
                         env, relocated, logs, report['checks'], marker='FACTORY_CHARACTER_PASS')
            if evidence != core.evidence_key(path) or core.status(path)['qa'] != 'RUNTIME_CHECKED':
                raise _Blocked('Source/revision changed during export; rerun QA before exporting.')
            files = {p.name: core.digest(p) for p in [executable, pack]}
            manifest = {'format': 'LINUX_X86_64_NATIVE_EXECUTABLE', 'evidence': evidence,
                        'engine_version': report['engine_version'], 'template_sha256': report['template_sha256'],
                        'files': files, 'checks': report['checks'],
                        'visual_review': 'PENDING', 'hardware_review': 'PENDING'}
            core.write_json(output / 'manifest.json', manifest)
            archive = work / 'game-linux-x86_64.zip'
            with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as bundle:
                for artifact in sorted(output.iterdir()):
                    bundle.write(artifact, artifact.name)
            with zipfile.ZipFile(archive) as bundle:
                if bundle.testzip() is not None:
                    raise _Failed('Native ZIP checksum verification failed.')
            destination = path / 'dist/linux' / run_id
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copytree(output, destination)
            shutil.copy2(archive, destination / archive.name)
            report.update(status='NATIVE_CHECKED', executable=str(destination / executable.name),
                          pack=str(destination / pack.name), archive=str(destination / archive.name),
                          archive_sha256=core.digest(destination / archive.name), manifest=str(destination / 'manifest.json'))
    except _Blocked as error:
        report.update(status='BLOCKED', reason=str(error))
    except (_Failed, OSError, ValueError, KeyError, json.JSONDecodeError) as error:
        report.update(status='FAILED', reason=str(error))
    # Do not follow an unsafe report path even to record a rejection.
    if path.is_dir() and not (path / 'native.json').is_symlink() and not (path / 'native.tmp').is_symlink():
        core.write_json(path / 'native.json', report)
    return report
