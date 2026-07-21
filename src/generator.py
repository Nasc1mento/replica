import subprocess
import yaml

KNOWN_REMOTE_URLS = {
    'flathub': 'https://flathub.org/repo/flathub.flatpakrepo',
    'flathub-beta': 'https://flathub.org/beta-repo/flathub-beta.flatpakrepo',
    'gnome-nightly': 'https://nightly.gnome.org/gnome-nightly.flatpakrepo',
    'fedora': 'oci+https://registry.fedoraproject.org',
    'elementaryos': 'https://flatpak.elementary.io/repo.flatpakrepo'
}

GENERATORS = {}

def register(name, ext):
    def decorator(fn):
        GENERATORS[name] = {'fn': fn, 'ext': ext}
        return fn
    return decorator

def _run_flatpak(*args, raw=False, skip_header=True):
    result = subprocess.run(
        ['flatpak-spawn', '--host', 'flatpak', *args],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        return "" if raw else []
    if raw:
        return result.stdout.strip()
    lines = result.stdout.splitlines()
    if skip_header:
        lines = lines[1:]
    return [line.split() for line in lines]

def flatpak_apps():
    return [
        {'app_id': p[0], 'name': ' '.join(p[1:-3]), 'origin': p[-3], 'installation': p[-2], 'version': p[-1]}
        for p in _run_flatpak('list', '--app', '--columns=application,name,origin,installation,version')
    ]

def flatpak_remotes():
    return [
        {'name': p[0], 'url': p[1], 'options': p[2]}
        for p in _run_flatpak('remotes', '--columns=name,url,options', skip_header=False)
    ]

def flatpak_overrides(apps):
    return [
        {'app_id': app['app_id'], 'overrides': output}
        for app in apps
        if (output := _run_flatpak('override', '--show', app['app_id'], raw=True))
    ]

def parse_override_flags(override):
    app_id = override['app_id']
    section = None
    unset_vars = set()

    for line in override['overrides'].splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith('['):
            section = line[1:-1]
            continue

        key, _, value = line.partition('=')

        if section == 'Context':
            for item in value.rstrip(';').split(';'):
                if item:
                    if key.lower() == 'unset-environment':
                        unset_vars.add(item)
                    yield app_id, f"--{key.lower()}={item}"

        elif section == 'Environment':
            if key in unset_vars:
                continue
            if value:
                yield app_id, f"--env={key}={value}"
            else:
                yield app_id, f"--unset-env={key}"

        elif section == 'Session Bus Policy':
            if value == 'talk':
                yield app_id, f"--talk-name={key}"
            elif value == 'own':
                yield app_id, f"--own-name={key}"
            else:
                yield app_id, f"--no-talk-name={key}"

        elif section == 'System Bus Policy':
            if value == 'talk':
                yield app_id, f"--system-talk-name={key}"
            else:
                yield app_id, f"--system-own-name={key}"

def generate(generator_type: str):
    remotes = flatpak_remotes()
    apps = flatpak_apps()
    overrides = flatpak_overrides(apps)
    generator = GENERATORS.get(generator_type)
    entry = GENERATORS.get(generator_type)
    return entry['fn'](apps, remotes, overrides), entry['ext']

@register("Ansible Playbook", ".yml")
def generate_playbook(apps, remotes, overrides):
    tasks = []

    for remote in remotes:
        uri = KNOWN_REMOTE_URLS.get(remote['name'], remote['url'])
        tasks.append({
            'name': f"Add remote {remote['name']}",
            'community.general.flatpak_remote': {
                'name': remote['name'],
                'state': 'present',
                'flatpakrepo_url': uri,
                'method': remote['options'],
            }
        })

    for app in apps:
        tasks.append({
            'name': f"Install {app['name']}",
            'community.general.flatpak': {
                'name': f"{app['app_id']}//{app['version']}",
                'state': 'present',
                'remote': app['origin'],
                'method': app['installation'],
            }
        })

    for override in overrides:
        for app_id, flag in parse_override_flags(override):
            tasks.append({
                'name': f"Override {app_id} {flag}",
                'ansible.builtin.command': f"flatpak override {app_id} {flag}",
            })

    playbook = [{
        'name': 'Replica - Restore Flatpak Environment',
        'hosts': 'localhost',
        'become': False,
        'tasks': tasks,
    }]

    return yaml.dump(playbook, default_flow_style=False, allow_unicode=True, sort_keys=False)

@register("Shell Script", ".sh")
def generate_shell(apps, remotes, overrides):
    lines = ['#!/bin/bash', 'set -e', '']

    lines.append('# Remotes')
    for remote in remotes:
        uri = KNOWN_REMOTE_URLS.get(remote['name'], remote['url'])
        lines.append(f"flatpak remote-add --{remote['options']} --if-not-exists {remote['name']} {uri}")
    lines.append('')

    lines.append('# Apps')
    for app in apps:
        lines.append(f"flatpak install -y --{app['installation']} {app['origin']} {app['app_id']}//{app['version']}")
    lines.append('')

    lines.append('# Overrides')
    for override in overrides:
        for app_id, flag in parse_override_flags(override):
            lines.append(f"flatpak override {app_id} {flag}")

    return '\n'.join(lines)
