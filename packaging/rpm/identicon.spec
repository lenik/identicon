# Version is injected by packaging/rpm/Makefile via `zfr version`.
# RPM Version cannot contain '-'; use `zfr version -r` (hyphens → '_').
# srcversion is the unsanitized Meson/git version and names the tarball.
%{!?version:%global version 0.0.0}
%{!?srcversion:%global srcversion %{version}}

%global debug_package %{nil}

Name:           identicon
Version:        %{version}
Release:        1%{?dist}
Summary:        generate deterministic avatar images from an identifier

License:        AGPL-3.0-or-later AND MIT AND CC-BY-3.0 AND CC-BY-4.0 AND CC0-1.0
BuildArch:      noarch
URL:            https://github.com/lenik/identicon
Packager:       Lenik <identicon@bodz.net>
Source0:        %{name}-%{srcversion}.tar.xz

BuildRequires:  meson
BuildRequires:  ninja-build
BuildRequires:  python3
BuildRequires:  gettext
BuildRequires:  asciidoctor

Requires:       python3
Requires:       python3-pillow

%description
identicon renders a square avatar from an ID string. Supported styles
include kaleidoscopic identicons, cartoon wavatars, pixel monsters,
8-bit retro faces, small robots, and Robohash sets 1 through 6.
Output may be PNG, JPEG, GIF, or BMP, to a file or standard output.

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
%{_bindir}/*.py
%{_datadir}/bash-completion/completions/identicon
%{_mandir}/man1/identicon.1*
%{_mandir}/*/man1/identicon.1*
%{_datadir}/locale/*/LC_MESSAGES/identicon.mo
%{_datadir}/doc/identicon/
%{_datadir}/identicon/
%changelog
* Thu Aug 20 2026 Lenik <identicon@bodz.net>
- Align spec with debian/control (Meson, AGPL-3.0-or-later).
- Version comes from `zfr version`, the same method meson.build uses.
