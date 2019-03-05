%global optflags %{optflags} -std=gnu++14 -Wno-gnu-statement-expression
%define major %(echo %{version} |cut -d. -f1)
%define libname %mklibname v8 %{major}
%define devname %mklibname -d v8

Name:		v8
Version:	7.4.284
Release:	1
Summary:	JavaScript Engine
Group:		System/Libraries
License:	BSD
URL:		https://chromium.googlesource.com/v8/v8/
# To make the source, you need to have depot_tools installed and in your PATH
# Also, python 2.x needs to be ahead of python 3.x in the PATH for now
# https://chromium.googlesource.com/chromium/tools/depot_tools.git/+archive/7e7a454f9afdddacf63e10be48f0eab603be654e.tar.gz
# Note that the depot_tools tarball above does not unpack into its own directory.
# mkdir v8-tmp
# cd v8-tmp
# fetch v8
# cd v8
# git checkout %{version}
# gclient sync
# cd ..
# mv v8 v8-%{version}
# tar -c --exclude=build/linux --exclude third_party/icu --exclude third_party/binutils --exclude third_party/llvm-build -J -f v8-%{version}.tar.xz v8-%{version}
Source0:	v8-%{version}.tar.xz
Patch0:		v8-7.4.268-soname.patch
Patch1:		v8-7.4.268-system-icu.patch
ExclusiveArch:	%{ix86} %{x86_64} ppc ppc64 %{arm} %{aarch64} %{mips} s390 s390x
Requires:	%{libname} = %{EVRD}
BuildRequires:	pkgconfig(icu-uc)
BuildRequires:	pkgconfig(glib-2.0)
BuildRequires:	pkgconfig(gmodule-2.0)
BuildRequires:	pkgconfig(gobject-2.0)
BuildRequires:	pkgconfig(gthread-2.0)
BuildRequires:	readline-devel
BuildRequires:	python2-devel
BuildRequires:	clang
BuildRequires:	ninja
BuildRequires:	lld

%description
V8 is Google's open source JavaScript engine. V8 is written in C++ and is used 
in Google Chrome, the open source browser from Google. V8 implements ECMAScript 
as specified in ECMA-262, 3rd edition.

%package -n %{libname}
Group:		System/Libraries
Summary:	Shared library for the v8 JavaScript engine
Requires:	%{name} = %{EVRD}

%description -n %{libname}
Shared library for the v8 JavaScript engine

%package -n %{devname}
Group:		Development/C++
Summary:	Development headers and libraries for v8
Requires:	%{libname} = %{EVRD}
Provides:	v8-devel = %{EVRD}

%description -n %{devname}
Development headers and libraries for v8.

%package -n python2-%{name}
Summary:	Python libraries from v8
Requires:	%{name} = %{EVRD}
Group:		Development/Python

%description -n python2-%{name}
Python libraries from v8.

%prep
%setup -q -n %{name}-%{version}
%apply_patches

rm -rf build/linux/debian* third_party/icu

ln -s /usr/bin/python2 python
export PATH=`pwd`:$PATH

%build
export PATH=`pwd`:$PATH:$(pwd)/third_party/depot_tools
%ifarch %{x86_64}
%global v8arch x64
%endif
%ifarch %{ix86}
%global v8arch ia32
%endif
%ifarch %{arm}
%global v8arch arm
%endif
%ifarch %{aarch64}
%global v8arch arm64
%endif
%ifarch mips
%global v8arch mips
%endif
%ifarch mipsel
%global v8arch mipsel
%endif
%ifarch mips64
%global v8arch mips64
%endif
%ifarch mips64el
%global v8arch mips64el
%endif
%ifarch ppc
%global v8arch ppc
%endif
%ifarch ppc64
%global v8arch ppc64
%endif
%ifarch s390
%global v8arch s390
%endif
%ifarch s390x
%global v8arch s390x
%endif

mkdir -p out/Release
cat >out/Release/args.gn <<EOF
binutils_path="%{_bindir}"
clang_base_path="%{_prefix}"
clang_use_chrome_plugins=false
enable_precompiled_headers=true
is_clang=true
is_desktop_linux=true
is_official_build=true
linux_use_bundled_binutils=false
proprietary_codecs=true
system_libdir="%{_lib}"
target_sysroot=""
treat_warnings_as_errors=false
use_aura=true
use_custom_libcxx=false
use_custom_libcxx_for_host=false
use_dbus=true
use_gold=true
use_icf=true
use_sysroot=false
v8_enable_embedded_binutils=false
v8_enable_i18n_support=true
is_cfi=false
use_thin_lto=false
is_component_build=true
v8_component_build=true
EOF
gn gen out/Release
%ninja_build -C out/Release

%install
# Sadly, no install target provided...

pushd out/Release
# library first
mkdir -p %{buildroot}%{_libdir}
cp -a libv8*.so.%{major} %{buildroot}%{_libdir}
# Next, binaries
mkdir -p %{buildroot}%{_bindir}
install -p -m0755 {d8,v8_shell} %{buildroot}%{_bindir}
# install -p -m0755 mksnapshot %{buildroot}%{_bindir}
# install -p -m0755 parser_fuzzer %{buildroot}%{_bindir}
# BLOBS! (Don't stress. They get built out of source code.)
install -p natives_blob.bin snapshot_blob.bin %{buildroot}%{_libdir}
popd

# Now, headers
mkdir -p %{buildroot}%{_includedir}
install -p include/*.h %{buildroot}%{_includedir}
cp -a include/libplatform %{buildroot}%{_includedir}
# Are these still useful?
mkdir -p %{buildroot}%{_includedir}/v8/extensions/
install -p src/extensions/*.h %{buildroot}%{_includedir}/v8/extensions/

# Make shared library links
pushd %{buildroot}%{_libdir}
for i in v8 v8_libplatform v8_libbase v8_for_testing; do
	ln -sf lib${i}.so.%{major} lib${i}.so
done
popd

# install Python JS minifier scripts for nodejs
install -d %{buildroot}%{py2_puresitedir}
install -p -m0744 tools/js2c.py %{buildroot}%{py2_puresitedir}/
chmod -R -x %{buildroot}%{py2_puresitedir}/*.py*

%files
%doc AUTHORS ChangeLog
%{_bindir}/d8
%{_bindir}/v8_shell
%{_libdir}/*.bin

%files -n %{libname}
%{_libdir}/libv8.so.%{major}
%{_libdir}/libv8_libbase.so.%{major}
%{_libdir}/libv8_libplatform.so.%{major}
%{_libdir}/libv8_for_testing.so.%{major}

%files -n %{devname}
%{_includedir}/*.h
%{_includedir}/libplatform/
%dir %{_includedir}/v8/
%{_includedir}/v8/extensions/
%{_libdir}/libv8.so
%{_libdir}/libv8_libbase.so
%{_libdir}/libv8_libplatform.so
%{_libdir}/libv8_for_testing.so

%files -n python2-%{name}
%{py2_puresitedir}/j*.py*
