%global optflags %{optflags} -std=gnu++14 -Wno-gnu-statement-expression
%global major %(echo %{version} |cut -d. -f1)
%define libname %mklibname v8 %{major}
%define devname %mklibname -d v8

Name:		v8
Version:	6.1.216
Release:	2
Summary:	JavaScript Engine
Group:		System/Libraries
License:	BSD
URL:		https://chromium.googlesource.com/v8/v8/
# To make the source, you need to have depot_tools installed and in your PATH
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
# tar -c  --exclude=.git --exclude=build/linux --exclude third_party/binutils --exclude third_party/llvm-build -J -f v8-%{version}.tar.xz v8-%{version}
Source0:	v8-%{version}.tar.xz
Patch0:		v8-4.10.91-system_icu.patch
Patch1:		v8-6.1.216-remove-system-libs.patch
Patch2:		v8-5.2.258-bundled-binutils.patch
Patch3:		v8-5.6.331-soversions.patch
ExclusiveArch:	%{ix86} x86_64 ppc ppc64 %{arm} aarch64 %{mips} s390 s390x
Requires:	%{libname} = %{EVRD}
BuildRequires:	pkgconfig(icu-uc)
BuildRequires:	readline-devel
BuildRequires:	python2-devel
BuildRequires:	clang

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

ln -s /usr/bin/python2 python
export PATH=`pwd`:$PATH

# Don't make thin libraries. :(
for i in `find . -type f -name '*.mk'`; do sed -i 's|alink_thin|alink|g' $i; done
sed -i "s|'alink_thin'|'alink'|g" tools/gyp/pylib/gyp/generator/make.py
sed -i "s|'alink_thin'|'alink'|g" tools/gyp/pylib/gyp/generator/ninja.py
#sed -i "s|crsT|crs|g" out/Makefile
sed -i "s|crsT|crs|g" tools/gyp/pylib/gyp/generator/make.py
sed -i -e '/available targets:/iGYPFLAGS+=-Duse_sysroot=0' Makefile

%build
export PATH=`pwd`:$PATH
%ifarch x86_64
%global v8arch x64
%endif
%ifarch %{ix86}
%global v8arch ia32
%endif
%ifarch %{arm}
%global v8arch arm
%endif
%ifarch aarch64
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

make %{v8arch}.release \
%ifarch armv7hl armv7hnl
armfloatabi=hard \
%endif
%ifarch armv5tel armv6l armv7l
armfloatabi=softfp \
%endif
system_icu=on \
soname_version=%{major} \
snapshot=external \
library=shared %{?_smp_mflags} \
bundledbinutils=off \
CC=%{_bindir}/clang \
CXX=%{_bindir}/clang++ \
CFLAGS="%{optflags}" \
CXXFLAGS="%{optflags}" \
LDFLAGS="%{optflags}" \
V=1

%install
pushd out/%{v8arch}.release
# library first
mkdir -p %{buildroot}%{_libdir}
cp -a lib.target/libv8*.so.%{major} %{buildroot}%{_libdir}
# Now, the static libraries that some/most/all v8 applications also need to link against.
cp -a obj.target/src/libv8_*.a %{buildroot}%{_libdir}
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
for i in v8 v8_libplatform v8_libbase; do
	ln -sf lib${i}.so.%{major} lib${i}.so
done
popd

# install Python JS minifier scripts for nodejs
install -d %{buildroot}%{python_sitelib}
sed -i 's|/usr/bin/python2.4|/usr/bin/env python2|g' tools/jsmin.py
sed -i 's|/usr/bin/python2.4|/usr/bin/env python2|g' tools/js2c.py
install -p -m0744 tools/jsmin.py %{buildroot}%{python_sitelib}/
install -p -m0744 tools/js2c.py %{buildroot}%{python_sitelib}/
chmod -R -x %{buildroot}%{python_sitelib}/*.py*

%post -p /sbin/ldconfig

%postun -p /sbin/ldconfig

%files
%doc AUTHORS ChangeLog
%{_bindir}/d8
%{_bindir}/v8_shell
%{_libdir}/*.bin

%files -n %{libname}
%{_libdir}/libv8.so.%{major}
%{_libdir}/libv8_libbase.so.%{major}
%{_libdir}/libv8_libplatform.so.%{major}

%files -n %{devname}
%{_includedir}/*.h
%{_includedir}/libplatform/
%dir %{_includedir}/v8/
%{_includedir}/v8/extensions/
%{_libdir}/libv8.so
%{_libdir}/libv8_libbase.so
%{_libdir}/libv8_libplatform.so
%{_libdir}/*.a

%files -n python2-%{name}
%{python_sitelib}/j*.py*
