project(
    'identicon',
    version: run_command(
        'sh',
        '-c', '''
        v=$(
            command -v zfr >/dev/null 2>&1 && zfr version 2>/dev/null || true
        )
        if [ -z "$v" ] && [ -f VERSION ]; then
            v=$(head -n1 VERSION | tr -d '\r')
            v=${v#v}
        fi
        if [ -z "$v" ]; then
            v="0.0.0" # FIXED TO 0.0.0, DO NOT MODIFY
        fi
        printf '%s' "$v"
        ''',
        check: false,
    ).stdout().strip(),
    license: 'AGPL-3.0-or-later',
)

project_author = 'Lenik'
project_email = 'identicon@bodz.net'
project_year = 2026

py = import('python').find_installation('python3')
fs = import('fs')
asciidoctor = find_program('asciidoctor', required: true)

prefix = get_option('prefix')
bindir = prefix / get_option('bindir')
datadir = prefix / get_option('datadir')
localedir = prefix / get_option('localedir')
mandir = prefix / get_option('mandir')
pkgdocdir = datadir / 'doc' / meson.project_name()

subdir('po')

identicon_exe = custom_target(
    'identicon',
    input: 'src/identicon.py',
    output: 'identicon',
    command: [
        py,
        '-c',
        'import os, shutil, sys; shutil.copyfile(sys.argv[1], sys.argv[2]); os.chmod(sys.argv[2], 0o755)',
        '@INPUT@',
        '@OUTPUT@',
    ],
    build_by_default: true,
    install: true,
    install_dir: bindir,
)

foreach mod : [
    'runtime.py',
    'pixgrid.py',
    'ident_style.py',
    'wavatar_style.py',
    'monster_style.py',
    'retro_style.py',
    'robo_style.py',
    'robohash_style.py',
    'styles.py',
]
    custom_target(
        mod,
        input: 'src' / mod,
        output: mod,
        command: ['cp', '@INPUT@', '@OUTPUT@'],
        build_by_default: true,
        install: true,
        install_dir: bindir,
    )
endforeach

install_subdir(
    'third_party' / 'robohash',
    install_dir: datadir / 'identicon',
    follow_symlinks: false,
)

install_data(
    'identicon.bash',
    install_dir: datadir / 'bash-completion' / 'completions',
    rename: 'identicon',
)

install_data(
    [
        'LICENSE',
        'README.md',
        'README-zh_CN.md',
    ],
    install_dir: pkgdocdir,
)

test(
    'python-unit',
    py,
    args: ['-m', 'unittest', 'discover', '-s', (meson.project_source_root() / 'tests'), '-p', 'test_*.py'],
    env: [
        'PYTHONPATH=' + (meson.project_source_root() / 'src'),
        'IDENTICON_LOCALEDIR=' + (meson.project_build_root() / 'po'),
        'IDENTICON_ROBOHASH_DIR=' + (meson.project_source_root() / 'third_party' / 'robohash'),
    ],
)

run_target(
    'posync',
    command: [
        find_program('zfr'),
        'translate',
        '--sync',
        '-C', meson.project_source_root(),
    ],
)

run_target(
    'look',
    command: [
        find_program('zfr'),
        'build',
        '--look',
        '-C', meson.project_source_root(),
        '-b', meson.project_build_root(),
    ],
)

run_target(
    'install-symlinks',
    command: [
        'bash',
        meson.project_source_root() / 'scripts' / 'install-symlinks.sh',
        meson.project_source_root(),
        meson.project_build_root(),
        get_option('prefix'),
        bindir,
        datadir,
        mandir,
    ],
)

run_target(
    'uninstall-symlinks',
    command: [
        'bash',
        meson.project_source_root() / 'scripts' / 'uninstall-symlinks.sh',
        meson.project_source_root(),
        meson.project_build_root(),
        get_option('prefix'),
        bindir,
        datadir,
        mandir,
    ],
)

puffs = [
    'identicon',
]
foreach puff : puffs
  custom_target(
    puff + '-man',
    input: 'man' / (puff + '.adoc'),
    output: puff + '.1',
    command: [
      asciidoctor,
      '-b', 'manpage',
      '-a', 'project-version=' + meson.project_version(),
      '-a', 'project-year=@0@'.format(project_year),
      '-a', 'project-author=' + project_author,
      '-a', 'project-email=' + project_email,
      '-o', '@OUTPUT@',
      '@INPUT@',
    ],
    build_by_default: true,
    install: true,
    install_dir: mandir / 'man1',
  )
endforeach

man_locales = [
    'ar',
    'de',
    'es',
    'fr',
    'it',
    'ja',
    'ko',
    'zh_CN',
]
foreach loc : man_locales
  man_loc = custom_target(
    'identicon-man-' + loc,
    input: 'man' / loc / 'identicon.adoc',
    output: 'identicon-' + loc + '.1',
    command: [
      asciidoctor,
      '-b', 'manpage',
      '-a', 'project-version=' + meson.project_version(),
      '-a', 'project-year=@0@'.format(project_year),
      '-a', 'project-author=' + project_author,
      '-a', 'project-email=' + project_email,
      '-o', '@OUTPUT@',
      '@INPUT@',
    ],
    build_by_default: true,
  )
  meson.add_install_script(
    py,
    '-c',
    'import os, shutil, sys; src, rel = sys.argv[1], sys.argv[2]; root = os.environ.get("MESON_INSTALL_DESTDIR_PREFIX") or os.environ["MESON_INSTALL_PREFIX"]; dest = os.path.join(root, rel); os.makedirs(os.path.dirname(dest), exist_ok=True); shutil.copy2(src, dest)',
    man_loc,
    fs.relative_to(mandir, prefix) / loc / 'man1' / 'identicon.1',
  )
endforeach
