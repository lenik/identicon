# Version is injected by packaging/rpm/Makefile via `zfr version`.
# RPM Version cannot contain '-'; use `zfr version -r` (hyphens → '_').
# srcversion is the unsanitized Meson/git version and names the tarball.
%{!?version:%global version 0.0.0}
%{!?srcversion:%global srcversion %{version}}

Name:           identicon
Version:        %{version}
Release:        1%{?dist}
Summary:        Meson-based CLI project template with example app

License:        AGPL-3.0-or-later
URL:            https://github.com/lenik/identicon
Packager:       Lenik <identicon@bodz.net>
Source0:        %{name}-%{srcversion}.tar.xz

BuildRequires:  meson
BuildRequires:  ninja-build
BuildRequires:  python3
BuildRequires:  gettext
BuildRequires:  asciidoctor

Requires:       python3

%description
identicon is a template repository for small Python command-line utilities.
It currently ships the identicon example application and Debian packaging
metadata, and includes Python unittest integration.

%prep
%setup -q -n %{name}-%{srcversion}

%build
meson setup build \
    --prefix=%{_prefix} \
    --bindir=%{_bindir} \
    --datadir=%{_datadir} \
    --mandir=%{_mandir} \
    --sysconfdir=%{_sysconfdir} \
    --localstatedir=%{_localstatedir} \
    --buildtype=plain
meson compile -C build

%install
meson install -C build --destdir=%{buildroot}

%files
%{_bindir}/identicon
%{_bindir}/common_lib.py
%{_datadir}/bash-completion/completions/identicon
%{_mandir}/man1/identicon.1*
%{_datadir}/doc/%{name}/
%{_datadir}/locale/*/LC_MESSAGES/identicon.mo

%changelog
* Thu Aug 20 2026 Lenik <identicon@bodz.net>
- Align spec with debian/control (Meson, AGPL-3.0-or-later).
- Version comes from `zfr version`, the same method meson.build uses.
