#
# V-Ray/Blender Build System
#
# http://vray.cgdo.ru
#
# Author: Andrey M. Izrantsev (aka bdancer)
# E-Mail: izrantsev@cgdo.ru
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# All Rights Reserved. V-Ray(R) is a registered trademark of Chaos Software.
#


import os
import sys
import glob
import shutil
import subprocess
import inspect

from .builder import utils
from .builder import Builder

PYTHON_VERSION     = "3.6.2"
PYTHON_VERSION_BIG = "3.6"
NUMPY_VERSION      = "1.13.1"
BOOST_VERSION      = "1.60.0"
OCIO_VERSION       = "1.0.9"
OPENEXR_VERSION    = "2.2.0"
ILMBASE_VERSION    = "2.2.0"
OIIO_VERSION       = "1.7.15"
LLVM_VERSION       = "3.4"
TIFF_VERSION       = "3.9.7"
FFTW_VERSION       = "3.3.4"
OSL_VERSION        = "1.7.5"
FFMPEG_VERSION     = "3.2.1"
GIFLIB_VERSION     = "5.1.4"
WEBP_VERSION       = "0.6.0"
PNG_VERSION        = "1.2.59"
PCRE_VERSION       = "8.32"
LIBXML_VERSION     = "2.9.7"
COLLADA_VERSION    = "1.6.51"
COLLADA_UID        = "0c2cdc17c22cf42050e4d42154bed2176363549c"

LIBS_PREFIX = None
LIBS_GENERATION = 29


def getLibPath(name, *subdirs):
	"""Get correct install dir for library uising global var for version
	and append any subdirs/filenames passed"""
	if not LIBS_PREFIX:
		sys.stderr.write("LIBS_PREFIX must be set before getLibPath is used")
		sys.stderr.flush()
		sys.exit(-1)

	varName = name.upper() + "_VERSION"
	if varName not in globals():
		sys.stderr.write("Can't find prefix for '%s'" % name)
		sys.stderr.flush()
		sys.exit(-1)

	libDir = name + '-' + globals()[varName]
	return os.path.join(LIBS_PREFIX, libDir, *subdirs)


def getDepsCompilationData(self, prefix, wd, jobs):
	common_cmake_args = [
	"-D JPEG_LIBRARY=%s" % os.path.join(self.dir_source, 'blender-for-vray-libs', 'Linux', 'jpeg-turbo', 'lib', 'Release', 'libjpeg-turbo.a'),
	"-D JPEG_INCLUDE_DIR=%s" % os.path.join(self.dir_source, 'blender-for-vray-libs', 'Linux', 'jpeg-turbo', 'include'),
	"-D TIFF_LIBRARY=%s" % os.path.join(prefix, 'tiff-%s' % TIFF_VERSION, 'lib' 'libtiff.a'),
	"-D TIFF_INCLUDE_DIR=%s" % os.path.join(prefix, 'tiff-%s' % TIFF_VERSION, 'include'),
	]

	def getCmakeCommandStr(*additionalArgs):
		return ' '.join(['cmake'] + common_cmake_args + list(additionalArgs))

	def dbg(x):
		sys.stdout.write('%s\n' % x)
		sys.stdout.flush()
		return True

	def getChDirCmd(newDir):
		return lambda: os.chdir(newDir) or True

	def getDownloadCmd(url, name):
		def downloadFn():
			utils.stdout_log('wget -c "%s" -O %s' % (url, name))
			if os.path.exists(name):
				utils.stdout_log('file [%s] exists, will remove' % name)
				utils.remove_file(name)
			return 0 == os.system('wget -c "%s" -O %s' % (url, name))
		return downloadFn

	def patchOpenEXRCmake():
		with open(os.path.join(wd, 'OpenEXR-%s' % OPENEXR_VERSION, 'IlmImf', 'CMakeLists.txt'), 'r+') as f:
			content = [l.rstrip('\n') for l in f.readlines()]
			sys.stdout.write("Swapping lines: \n\t%s\n\t%s\n" % (content[27], content[28]))
			content[27], content[28] = content[28], content[27]
			f.seek(0)
			f.write('\n'.join(content))
			f.truncate()
		return True

	def patchLLVMCmake():
		with open(os.path.join(wd, 'LLVM-%s' % LLVM_VERSION, 'CMakeLists.txt'), 'r+') as f:
			content = [l.rstrip('\n') for l in f.readlines()]
			# set(PACKAGE_VERSION "${LLVM_VERSION_MAJOR}.${LLVM_VERSION_MINOR}svn")
			content[16] = '  set(PACKAGE_VERSION "${LLVM_VERSION_MAJOR}.${LLVM_VERSION_MINOR}")'
			f.seek(0)
			f.write('\n'.join(content))
			f.truncate()
		return True

	def getOrCmd(a, b):
		return lambda: a() or b()

	def removeSoFile(path):
		if os.path.isfile(path):
			dbg('Removing so file [%s]' % path)
			os.remove(path)
			return True
		return False

	def getRemoveSoFiles(dir):
		return lambda: all([removeSoFile(path) for path in glob.glob('%s/*.so*')])

	steps = (
		('python', '%s/python-%s' % (prefix, PYTHON_VERSION), (
			getChDirCmd(wd),
			getDownloadCmd("https://www.python.org/ftp/python/%s/Python-%s.tgz" % (PYTHON_VERSION, PYTHON_VERSION), 'python.tgz'),
			'tar -C . -xf python.tgz',
			getChDirCmd(os.path.join(wd, 'Python-%s' % PYTHON_VERSION)),
			'./configure --prefix=%s/python-%s --libdir=%s/python-%s/lib --enable-ipv6 --enable-loadable-sqlite-extensions --with-dbmliborder=bdb --with-computed-gotos --with-pymalloc --with-ensurepip=install'
				% (prefix, PYTHON_VERSION, prefix, PYTHON_VERSION),
			'make -j %s' % jobs,
			'make install',
			'ln -s %s/python-%s %s/python' % (prefix, PYTHON_VERSION, prefix),
			'ln -s %s/python-%s %s/python-%s' % (prefix, PYTHON_VERSION, prefix, PYTHON_VERSION_BIG),
		)),
		('requests', '%s/python/lib/python%s/site-packages/requests/api.py' % (prefix, PYTHON_VERSION_BIG), (
			'%s/python/bin/pip%s install requests' % (prefix, PYTHON_VERSION_BIG),
		)),
		('numpy', '%s/python/lib/python%s/site-packages/numpy' % (prefix, PYTHON_VERSION_BIG), (
			getChDirCmd(wd),
			getDownloadCmd("https://github.com/numpy/numpy/releases/download/v%s/numpy-%s.tar.gz" % (NUMPY_VERSION, NUMPY_VERSION), 'numpy.tar.gz'),
			'tar -C . -xf numpy.tar.gz',
			getChDirCmd(os.path.join(wd, 'numpy-%s' % NUMPY_VERSION)),
			'%s/python/bin/python3 setup.py install --old-and-unmanageable --prefix=%s/numpy-%s' % (prefix, prefix, NUMPY_VERSION),
			'ln -sf %s/numpy-%s %s/numpy' % (prefix, NUMPY_VERSION, prefix)
			#'mv %s/numpy-%s %s/numpy' % (prefix, NUMPY_VERSION, prefix) # move numpy because cmake will append numpy to the path given
		)),
		('boost', '%s/boost-%s' % (prefix, BOOST_VERSION),(
			getChDirCmd(wd),
			getDownloadCmd("http://sourceforge.net/projects/boost/files/boost/%s/boost_%s.tar.bz2/download" % (BOOST_VERSION, BOOST_VERSION.replace('.', '_')), 'boost.tar.bz2'),
			'tar -C . --transform "s,(.*/?)boost_1_[^/]+(.*),\\1boost-%s\\2,x" -xf boost.tar.bz2' % BOOST_VERSION,
			getChDirCmd(os.path.join(wd, 'boost-%s' % BOOST_VERSION)),
			'./bootstrap.sh',
			'./b2 -j %s -a --with-system --with-filesystem --with-thread --with-regex --with-locale --with-date_time --with-wave --prefix=%s/boost-%s --disable-icu boost.locale.icu=off install'
				% (jobs, prefix, BOOST_VERSION),
			'./b2 clean',
			'ln -s %s/boost-%s %s/boost' % (prefix, BOOST_VERSION, prefix),
			'sh -c "echo \"%s/boost/lib\" > /etc/ld.so.conf.d/boost.conf"' % prefix,
			'/sbin/ldconfig',
			getRemoveSoFiles('%s/boost/lib' % prefix)
		)),
		('png', '%s/png-%s' % (prefix, PNG_VERSION), (
			getChDirCmd(wd),
			getDownloadCmd('https://sourceforge.net/projects/libpng/files/libpng12/%s/libpng-%s.tar.xz/download' % (PNG_VERSION, PNG_VERSION), 'libpng-%s.tar.xz' % PNG_VERSION),
			'tar -C . -xf libpng-%s.tar.xz' % PNG_VERSION,
			getChDirCmd(os.path.join(wd, 'libpng-%s' % PNG_VERSION)),
			'./configure --prefix=%s/png-%s --enable-static=yes --enable-shared=no' % (prefix, PNG_VERSION),
			'make -j %s' % jobs,
			'make install',
			'ln -s %s/png-%s %s/png' % (prefix, PNG_VERSION, prefix),
		)),
		('tiff', '%s/tiff-%s' % (prefix, TIFF_VERSION), (
			getChDirCmd(wd),
			getDownloadCmd('http://download.osgeo.org/libtiff/tiff-%s.tar.gz' % TIFF_VERSION, 'tiff.tar.gz'),
			'tar -C . -xf tiff.tar.gz',
			getChDirCmd(os.path.join(wd, 'tiff-%s' % TIFF_VERSION)),
			'./configure --prefix=%s/tiff-%s --enable-static' % (prefix, TIFF_VERSION),
			'make -j %s' % jobs,
			'make  install',
			'ln -s %s/tiff-%s %s/tiff' % (prefix, TIFF_VERSION, prefix),
			'sh -c "echo \"%s/tiff/lib\" > /etc/ld.so.conf.d/tiff.conf"' % prefix,
			'/sbin/ldconfig'
		)),
		('fftw', '%s/fftw-%s' % (prefix, FFTW_VERSION), (
			getChDirCmd(wd),
			getDownloadCmd('http://www.fftw.org/fftw-%s.tar.gz' % FFTW_VERSION, 'fftw.tar.gz'),
			'tar -C . -xf fftw.tar.gz',
			getChDirCmd(os.path.join(wd, 'fftw-%s' % FFTW_VERSION)),
			'./configure --prefix=%s/fftw-%s --enable-static' % (prefix, FFTW_VERSION),
			'make -j %s' % jobs,
			'make  install',
			'ln -s %s/fftw-%s %s/fftw' % (prefix, FFTW_VERSION, prefix),
			'sh -c "echo \"%s/fftw/lib\" > /etc/ld.so.conf.d/fftw.conf"' % prefix,
			'/sbin/ldconfig'
		)),
		('ocio', '%s/ocio-%s' % (prefix, OCIO_VERSION), (
			getChDirCmd(wd),
			getDownloadCmd("https://github.com/imageworks/OpenColorIO/tarball/v%s" % OCIO_VERSION, 'ocio.tar.gz'),
			'tar -C . --transform "s,(.*/?)imageworks-OpenColorIO[^/]*(.*),\\1OpenColorIO-%s\\2,x" -xf ocio.tar.gz' % OCIO_VERSION,
			'mkdir -p OpenColorIO-%s/build' % OCIO_VERSION,
			getChDirCmd(os.path.join(wd, 'OpenColorIO-%s' % OCIO_VERSION, 'build')),
			' '.join(["cmake", "-D CMAKE_BUILD_TYPE=Release", "-D CMAKE_PREFIX_PATH=%s/ocio-%s" % (prefix, OCIO_VERSION),
					  "-D CMAKE_INSTALL_PREFIX=%s/ocio-%s" % (prefix, OCIO_VERSION), "-D OCIO_BUILD_APPS=OFF",
					  "-D OCIO_BUILD_PYGLUE=OFF", "-D CMAKE_CXX_FLAGS=\"-fPIC\"", "-D CMAKE_EXE_LINKER_FLAGS=\"-lgcc_s -lgcc\"", ".."]),
			'make -j %s' % jobs,
			'make install',
			'rm -f %s/ocio-%s/lib/*.so*' % (prefix, OCIO_VERSION),
			'cp ext/dist/lib/libtinyxml.a %s/ocio-%s/lib' % (prefix, OCIO_VERSION),
			'cp ext/dist/lib/libyaml-cpp.a %s/ocio-%s/lib' % (prefix, OCIO_VERSION),
			'make clean',
			'ln -s %s/ocio-%s %s/ocio' % (prefix, OCIO_VERSION, prefix),
			'sh -c "echo \"%s/ocio/lib\" > /etc/ld.so.conf.d/ocio.conf"' % prefix,
			'/sbin/ldconfig'
		)),
		('ilmbase', '%s/ilmbase-%s' % (prefix, ILMBASE_VERSION), (
			getChDirCmd(wd),
			getDownloadCmd("http://download.savannah.nongnu.org/releases/openexr/ilmbase-%s.tar.gz" % ILMBASE_VERSION, 'ilmbase.tar.gz'),
			'tar -C . --transform "s,(.*/?)ilmbase-[^/]*(.*),\\1ILMBase-%s\\2,x" -xf ilmbase.tar.gz' % ILMBASE_VERSION,
			'mkdir -p ILMBase-%s/build' % ILMBASE_VERSION,
			getChDirCmd(os.path.join(wd, 'ILMBase-%s' % ILMBASE_VERSION, 'build')),
			" ".join(["cmake", "-D CMAKE_BUILD_TYPE=Release", "-D CMAKE_PREFIX_PATH=%s/ilmbase-%s" % (prefix, ILMBASE_VERSION),
					  "-D CMAKE_INSTALL_PREFIX=%s/ilmbase-%s" % (prefix, ILMBASE_VERSION), "-D BUILD_SHARED_LIBS=OFF",
					  "-D NAMESPACE_VERSIONING=OFF", "-D CMAKE_CXX_FLAGS=\"-fPIC\"", "-D CMAKE_EXE_LINKER_FLAGS=\"-lgcc_s -lgcc\"", ".."]),
			'make -j %s' % jobs,
			'make install',
			'make clean',
		)),
		('openexr', '%s/openexr-%s' % (prefix, OPENEXR_VERSION), (
			getChDirCmd(wd),
			getDownloadCmd("http://download.savannah.nongnu.org/releases/openexr/openexr-%s.tar.gz" % OPENEXR_VERSION, 'openexr.tar.gz'),
			'tar -C . --transform "s,(.*/?)openexr[^/]*(.*),\\1OpenEXR-%s\\2,x" -xf openexr.tar.gz' % OPENEXR_VERSION,
			'mkdir -p OpenEXR-%s/build' % OPENEXR_VERSION,
			patchOpenEXRCmake,
			getChDirCmd(os.path.join(wd, 'OpenEXR-%s' % OPENEXR_VERSION, 'build')),
			' '.join(["cmake" , "-D CMAKE_BUILD_TYPE=Release", "-D CMAKE_PREFIX_PATH=%s/openexr-%s" % (prefix, OPENEXR_VERSION),
					  "-D CMAKE_INSTALL_PREFIX=%s/openexr-%s" % (prefix, OPENEXR_VERSION),
					  "-D ILMBASE_PACKAGE_PREFIX=%s/ilmbase-%s" % (prefix, ILMBASE_VERSION), "-D BUILD_SHARED_LIBS=OFF",
					  "-D NAMESPACE_VERSIONING=OFF", "-D CMAKE_CXX_FLAGS=\"-fPIC\"",  "-D CMAKE_EXE_LINKER_FLAGS=\"-lgcc_s -lgcc\"", ".."]),
			'make -j %s' % jobs,
			'make install',
			'make clean',
			'cp -Lrn %s/ilmbase-%s/* %s/openexr-%s' % (prefix, ILMBASE_VERSION, prefix, OPENEXR_VERSION),
			'ln -s %s/openexr-%s %s/openexr' % (prefix, OPENEXR_VERSION, prefix),
			'sh -c "echo \"%s/openexr/lib\" > /etc/ld.so.conf.d/openexr.conf"' % prefix,
			'/sbin/ldconfig'
		)),
		('oiio', '%s/oiio-%s' % (prefix, OIIO_VERSION), (
			getChDirCmd(wd),
			getDownloadCmd("https://github.com/OpenImageIO/oiio/archive/Release-%s.tar.gz" % OIIO_VERSION, 'oiio.tar.gz'),
			'mkdir -p OpenImageIO-%s' % OIIO_VERSION,
			'tar -C OpenImageIO-%s --strip-components=1 --transform "s,(.*/?)oiio-Release-[^/]*(.*),\\1OpenImageIO-%s\\2,x" -xf oiio.tar.gz'
				% (OIIO_VERSION, OIIO_VERSION),
			'mkdir -p OpenImageIO-%s/build' % OIIO_VERSION,
			getChDirCmd(os.path.join(wd, 'OpenImageIO-%s' % OIIO_VERSION, 'build')),
			getCmakeCommandStr(
				"-D CMAKE_BUILD_TYPE=Release", "-D CMAKE_PREFIX_PATH=%s" % prefix,
				"-D CMAKE_INSTALL_PREFIX=%s/oiio-%s" % (prefix, OIIO_VERSION),
				"-D STOP_ON_WARNING=OFF", "-D BUILDSTATIC=ON", "-D LINKSTATIC=ON", "-D USE_QT=OFF", "-D USE_PYTHON=OFF",
				"-D BUILD_TESTING=OFF", "-D OIIO_BUILD_TESTS=OFF", "-D OIIO_BUILD_TOOLS=OFF",
				"-D ILMBASE_VERSION=%s" % ILMBASE_VERSION ,"-D OPENEXR_VERSION=%s" % OPENEXR_VERSION,
				"-D ILMBASE_HOME=%s/openexr" % prefix, "-D OPENEXR_HOME=%s/openexr" % prefix,
				"-D BOOST_ROOT=%s/boost" % prefix, "-D Boost_NO_SYSTEM_PATHS=ON", "-D USE_OCIO=OFF",
				"-D CMAKE_CXX_FLAGS=\"-fPIC\"", "-D CMAKE_EXE_LINKER_FLAGS=\"-lgcc_s -lgcc\"", ".."
			),
			'make -j %s' % jobs,
			'make install',
			'make clean',
			'ln -s %s/oiio-%s %s/oiio' % (prefix, OIIO_VERSION, prefix),
			'sh -c "echo \"%s/oiio/lib\" > /etc/ld.so.conf.d/oiio.conf"' % prefix,
			'/sbin/ldconfig'
		)),
		('clang', '%s/llvm-%s' % (prefix, LLVM_VERSION), (
			getChDirCmd(wd),
			getDownloadCmd("http://llvm.org/releases/%s/llvm-%s.src.tar.gz" % (LLVM_VERSION, LLVM_VERSION), 'llvm.tar.gz'),
			getOrCmd(
				getDownloadCmd("http://llvm.org/releases/%s/clang-%s.src.tar.gz" % (LLVM_VERSION, LLVM_VERSION), 'clang.tar.gz'),
				getDownloadCmd("http://llvm.org/releases/%s/cfe-%s.src.tar.gz" % (LLVM_VERSION, LLVM_VERSION), 'clang.tar.gz')
			),
			'tar -C . --transform "s,([^/]*/?)llvm-[^/]*(.*),\\1LLVM-%s\\2,x" -xf llvm.tar.gz' % LLVM_VERSION,
			'tar -C LLVM-%s/tools --transform "s,([^/]*/?)(clang|cfe)-[^/]*(.*),\\1clang\\3,x" -xf clang.tar.gz' % LLVM_VERSION,
			'mkdir -p LLVM-%s/build' % LLVM_VERSION,
			getChDirCmd(os.path.join(wd, 'LLVM-%s' % LLVM_VERSION, 'build')),
			patchLLVMCmake,
			' '.join(["cmake", "-D CMAKE_BUILD_TYPE=Release",
					  "-D CMAKE_INSTALL_PREFIX=%s/llvm-%s" % (prefix, LLVM_VERSION),
					  "-D LLVM_TARGETS_TO_BUILD=X86",
					  "-D LLVM_ENABLE_TERMINFO=OFF", ".."]),
			'make -j %s' % jobs,
			'make install',
			'make clean',
		)),
		('osl', getLibPath('osl'), (
			getChDirCmd(wd),
			getDownloadCmd('https://github.com/imageworks/OpenShadingLanguage/archive/Release-%s.tar.gz' % OSL_VERSION, 'osl.tar.gz'),
			'tar -C . --transform "s,(.*/?)OpenShadingLanguage-[^/]*(.*),\\1OpenShadingLanguage-%s\\2,x" -xf osl.tar.gz' % (OSL_VERSION),
			'mkdir -p OpenShadingLanguage-%s/build' % OSL_VERSION,
			getChDirCmd(os.path.join(wd, 'OpenShadingLanguage-%s' % OSL_VERSION, 'build')),
			' '.join(["cmake", "-D CMAKE_BUILD_TYPE=Release","-D CMAKE_INSTALL_PREFIX=" + getLibPath('osl'),
					  "-DBUILD_TESTING=OFF","-DSTOP_ON_WARNING=OFF","-DBUILDSTATIC=ON",
					  "-DOSL_BUILD_PLUGINS=OFF","-DOSL_BUILD_TESTS=OFF","-DUSE_SIMD=sse2",
					  "-DOSL_BUILD_CPP11=1", "-DILMBASE_HOME=" + getLibPath('openexr'),
					  "-DILMBASE_CUSTOM=ON", "-DILMBASE_CUSTOM_LIBRARIES='Half;Iex;Imath;IlmThread'",
					  "-DBOOST_ROOT=" + getLibPath('boost'), "-DBoost_NO_SYSTEM_PATHS=ON",
					  "-DBoost_USE_STATIC_LIBS=ON", "-DOPENIMAGEIOHOME=" + getLibPath('oiio'),
					  "-DLLVM_VERSION=%s" % LLVM_VERSION, "-DLLVM_DIRECTORY=" + getLibPath('llvm'),
					  "-DLLVM_STATIC=ON", ".."]),
			'make -j %s' % jobs,
			'make install',
			'make clean',
			'ln -s %s %s/osl' % (getLibPath('osl'), prefix),
		)),
		('ffmpeg', getLibPath('ffmpeg'), (
			getChDirCmd(wd),
			getDownloadCmd("http://ffmpeg.org/releases/ffmpeg-%s.tar.bz2" % FFMPEG_VERSION, 'ffmpeg.tar.bz2'),
			'tar -C . -xf ffmpeg.tar.bz2',
			getChDirCmd(os.path.join(wd, 'ffmpeg-%s' % FFMPEG_VERSION)),
			' '.join(['./configure', '--cc="gcc -Wl,--as-needed"', '--extra-ldflags="-pthread -static-libgcc"',
					  '--prefix=%s' % getLibPath('ffmpeg'), '--enable-static', '--disable-ffplay',
					  '--disable-ffserver --disable-doc', '--enable-gray', '--enable-avfilter', '--disable-vdpau',
					  '--disable-bzlib', '--disable-libgsm', '--disable-libspeex', '--enable-pthreads',
					  '--enable-zlib', '--enable-stripping', '--enable-runtime-cpudetect', '--disable-vaapi',
					  '--disable-nonfree', '--enable-gpl', '--disable-postproc', '--disable-librtmp',
					  '--disable-libopencore-amrnb', '--disable-libopencore-amrwb', '--disable-libdc1394',
					  '--disable-version3', '--disable-outdev=sdl', '--disable-libxcb', '--disable-outdev=xv',
					  '--disable-indev=sndio', '--disable-outdev=sndio', '--disable-outdev=alsa',
					  '--disable-indev=sdl', '--disable-indev=alsa', '--disable-indev=jack', '--disable-indev=lavfi',
					  '--disable-yasm']),
			'make -j %s' % jobs,
			'make install',
			'make clean',
			'ln -s %s %s/ffmpeg' % (getLibPath('ffmpeg'), prefix),
		)),
		('giflib', getLibPath('giflib'), (
			getChDirCmd(wd),
			getDownloadCmd('http://downloads.sourceforge.net/giflib/giflib-%s.tar.bz2' % GIFLIB_VERSION, 'giflib.tar.bz2'),
			'tar -C . -xf giflib.tar.bz2',
			getChDirCmd(os.path.join(wd, 'giflib-%s' % GIFLIB_VERSION)),
			' '.join(['./configure', '--enable-static', '--prefix=%s' % getLibPath('giflib')]),
			'make -j %s' % jobs,
			'make install',
			'make clean',
		)),
		('webp', getLibPath('webp'),(
			getChDirCmd(wd),
			getDownloadCmd('https://storage.googleapis.com/downloads.webmproject.org/releases/webp/libwebp-%s-linux-x86-64.tar.gz' % WEBP_VERSION, 'webp.tar.gz'),
			'tar -C %s --transform "s,(.*/?)libwebp-[^/]*(.*),\\1%s\\2,x" -xf webp.tar.gz' % (prefix, os.path.basename(getLibPath('webp'))),
		)),
		('libxml2', getLibPath('libxml'), (
			getChDirCmd(wd),
			getDownloadCmd('https://git.gnome.org/browse/libxml2/snapshot/libxml2-%s.tar.xz' % LIBXML_VERSION, 'libxml.tar.xz'),
			'tar -C . -xf libxml.tar.xz',
			getChDirCmd(os.path.join(wd, 'libxml2-%s' % LIBXML_VERSION)),
			' '.join(['./autogen.sh', '--enable-static', '--disable-shared', '--without-python', '--prefix=%s' % getLibPath('libxml')]),
			'make -j %s' % jobs,
			'make install',
		)),
		('pcre', getLibPath('pcre'), (
			getChDirCmd(wd),
			getDownloadCmd('https://ftp.pcre.org/pub/pcre/pcre-%s.tar.gz' % PCRE_VERSION, 'pcre.tar.gz'),
			'tar -C . -xf pcre.tar.gz',
			getChDirCmd(os.path.join(wd, 'pcre-%s' % PCRE_VERSION)),
			' '.join(['./configure', '--prefix=%s' % getLibPath('pcre'), '--enable-static', '--disable-shared',
					  '--enable-pcre16', '--enable-pcre32', '--enable-unicode-properties']),
			'make -j %s' % jobs,
			'make install',
			'make clean',
		)),
		('collada', getLibPath('collada'), (
			getChDirCmd(wd),
			getDownloadCmd('https://github.com/KhronosGroup/OpenCOLLADA/archive/%s.zip' % COLLADA_UID, 'collada.zip'),
			'unzip -o collada.zip',
			'mkdir -p OpenCOLLADA-%s/build' % COLLADA_UID,
			getChDirCmd(os.path.join(wd, 'OpenCOLLADA-%s' % COLLADA_UID, 'build')),
			' '.join(['cmake', '../', '-DCMAKE_BUILD_TYPE=Release', '-DCMAKE_INSTALL_PREFIX=%s' % getLibPath('collada'),
					  '-DUSE_EXPATH=OFF', '-DUSE_LIBXML=ON', '-DUSE_STATIC=ON', '-DUSE_SHARED=OFF',
					  '-DCMAKE_PREFIX_PATH="%s;%s"' % (getLibPath('pcre'), getLibPath('libxml')),
					  '-DCMAKE_EXE_LINKER_FLAGS="-lz"']),
			'make -j %s' % jobs,
			'make install',
			'make clean',
		)),
	)

	return steps


def DepsBuild(self):
	prefix = self._blender_libs_location
	wd = self._blender_libs_wd

	global LIBS_PREFIX
	LIBS_PREFIX = prefix

	data = getDepsCompilationData(self, prefix, wd, self.build_jobs)

	if self.mode_test:
		# TODO: print out commands
		return

	sys.stdout.write('Building dependencies...\n')
	installed_python = False

	def alreadyInstalled(path):
		if not os.path.exists(path):
			return False

		content = utils.dir_contents_recursive(path)
		if len(content) == 0:
			return False

		return True

	for item in data:
		sys.stdout.write('Installing %s...' % item[0])
		shouldStop = False
		if alreadyInstalled(item[1]):
			if item[0] in ('numpy', 'requests') and installed_python:
				rm_cmd = 'rm -r %s/%s*' % (prefix, item[0])
				sys.stdout.write('We reinstalled python, removing %s with [%s] so we can reinstall it also\n' % (item[0], rm_cmd))
				sys.stdout.flush()
				os.system(rm_cmd)
			else:
				sys.stdout.write('%s already installed, skipping ...\n' % item[1])
				continue
		else:
			sys.stdout.write('%s missing - proceeding\n' % item[1])
			# we will install current item
			if item[0] == 'python':
				# if it is python save it
				installed_python = True
		sys.stdout.flush()

		fail = False
		for step in item[2]:
			sys.stdout.write("CWD %s\n" % os.getcwd())
			sys.stdout.flush()
			if callable(step):
				sys.stdout.write('Callable step: \n\t%s\n' % inspect.getsource(step).strip())
				sys.stdout.flush()
				if not step():
					fail = True
					break
				sys.stdout.write('\n')
			else:
				if self.jenkins and (step.endswith('ldconfig') or '/etc/ld.so.conf.d' in step):
					# lets skip system wide changes for jenkins
					sys.stdout.write('Skipping [%s] step because of jenkins flag!\n' % step)
				else:
					sys.stdout.write('Command step: \n\t%s\n' % step)
					sys.stdout.flush()
					res = subprocess.call(step, shell=True)
					sys.stderr.flush()
					if res != 0:
						fail = True
						break
		if fail:
			sys.stderr.write('Failed! Removing [%s] if it exists and stopping...\n' % item[1])
			sys.stderr.flush()
			if os.path.exists(item[1]):
				utils.remove_directory(item[1])
			sys.exit(-1)

	return True


class LinuxBuilder(Builder):

	def post_init(self):
		self.init_libs_prefix()
		if self.libs_need_clean():
			self.clean_prebuilt_libs()

		if DepsBuild(self):
			self.libs_update_cache_number()

		self.xpak_pak_install('CUDA9/1000')
		cudaRoot = os.path.join(self.xpak_path, 'CUDA9')
		cudaBinPath = os.path.join(cudaRoot, 'bin')
		utils.appendPathToEnvVariable('PATH', cudaBinPath)
		os.environ['CUDA_BIN_PATH'] = cudaBinPath
		utils.appendPathToEnvVariable('LD_LIBRARY_PATH', os.path.join(cudaRoot, 'lib', 'linux_x64'))
		utils.stdout_log('nvcc path: [%s]' % utils.which('nvcc'))


	def get_cache_num(self):
		return LIBS_GENERATION


	def compile(self):
		cmake_build_dir = os.path.join(self.dir_build, "blender-cmake-build")
		if self.build_clean and os.path.exists(cmake_build_dir):
			utils.remove_directory(cmake_build_dir)
		if not os.path.exists(cmake_build_dir):
			os.makedirs(cmake_build_dir)
		os.chdir(cmake_build_dir)

		distr_info = utils.get_linux_distribution()

		cmake = ['cmake']

		cmake.append("-G")
		cmake.append("Ninja")

		if self.gcc:
			cmake.append("-DCMAKE_C_COMPILER=%s" % self.gcc)
		if self.gxx:
			cmake.append("-DCMAKE_CXX_COMPILER=%s" % self.gxx)

		cmake.append("-DCMAKE_BUILD_TYPE=%s" % self.build_type.capitalize())
		cmake.append('-DCMAKE_INSTALL_PREFIX=%s' % self.dir_install_path)

		cmake.append("-DWITH_SYSTEM_GLEW=OFF")
		cmake.append("-DWITH_FFTW3=ON")
		cmake.append("-DWITH_ALEMBIC=ON")
		cmake.append("-DWITH_CXX11=ON")
		cmake.append("-DWITH_INPUT_NDOF=ON")
		cmake.append("-DWITH_X11_XINPUT=ON")
		cmake.append("-DWITH_INTERNATIONAL=ON")
		cmake.append("-DWITH_PYTHON_INSTALL=ON")
		cmake.append("-DWITH_PYTHON_INSTALL_NUMPY=ON")

		cmake.append("-DWITH_VRAY_FOR_BLENDER=ON")
		cmake.append("-DWITH_MANUAL_BUILDINFO=%s" % utils.GetCmakeOnOff(self.jenkins))
		cmake.append('-DWITH_STATIC_LIBC=%s' % utils.GetCmakeOnOff(self.with_static_libc))

		if self.build_mode == 'nightly':
			cmake.append("-DLIBS_ROOT=%s" % utils.path_join(self.dir_source, 'blender-for-vray-libs'))

		cmake.append("-DWITH_GAMEENGINE=%s" % utils.GetCmakeOnOff(self.with_ge))
		cmake.append("-DWITH_PLAYER=%s" % utils.GetCmakeOnOff(self.with_player))
		cmake.append("-DWITH_LIBMV=%s" % utils.GetCmakeOnOff(self.with_tracker))
		cmake.append("-DWITH_OPENCOLLADA=%s" % utils.GetCmakeOnOff(self.with_collada))
		cmake.append("-DWITH_CYCLES=%s" % utils.GetCmakeOnOff(self.with_cycles))
		if self.with_cycles:
			cmake.append("-DWITH_CODEC_FFMPEG=ON")
			cmake.append("-DFFMPEG_LIBRARIES='avformat;avcodec;avutil;avdevice;swscale;swresample;rt'")
			cmake.append("-DWITH_OPENCOLORIO=ON")
			cmake.append("-DWITH_OPENIMAGEIO=ON")
			cmake.append("-DWITH_LLVM=ON")
			cmake.append("-DLLVM_STATIC=ON")
			cmake.append("-DWITH_CYCLES_CUDA=ON")
			cmake.append("-DWITH_CYCLES_CUDA_BINARIES=ON")
			cudaRoot = os.path.join(self.xpak_path, 'CUDA9')
			cmake.append("-DCUDA_TOOLKIT_ROOT_DIR=%s" % cudaRoot)
			cmake.append("-DCUDA_TOOLKIT_TARGET_DIR=%s" % cudaRoot)
			cmake.append("-DCUDA_NVCC_EXECUTABLE=%s" % os.path.join(cudaRoot, 'bin', 'nvcc'))
			cmake.append("-DCUDA_CUDART_LIBRARY=%s" % os.path.join(cudaRoot, 'lib', 'linux_x64', 'libcudart.so.9.0.176'))
			cmake.append("-DCUDA_TOOLKIT_INCLUDE=%s" % os.path.join(cudaRoot, 'include'))

			cmake.append("-DWITH_CYCLES_OSL=ON")

		cmake.append("-DWITH_MOD_OCEANSIM=ON")
		cmake.append("-DWITH_OPENSUBDIV=ON")
		cmake.append("-DWITH_STATIC_LIBS=ON")

		libs_prefix = '/opt/lib' if utils.get_linux_distribution()['short_name'] == 'centos' else '/opt'

		if hasattr(self, '_blender_libs_location'):
			libs_prefix = self._blender_libs_location

		if self.jenkins:
			sys.stdout.write('Removing boost so files ...\n')
			sys.stdout.flush()
			for f in glob.glob('%s/boost/lib/*.so*' % libs_prefix):
				sys.stdout.write('Removing so [%s]\n' % f)
				sys.stdout.flush()
				os.remove(f)

		if self.dev_static_libs:
			if distr_info['short_name'] == 'centos' or self.jenkins:

				cmake.append("-DLIBDIR=%s" % libs_prefix)

				# NOTES:
				#   OpenJPEG is disabled in OpenImageIO
				#   Smth wrong with OpenAL headers - disabling
				#
				cmake.append("-DWITH_OPENAL=OFF")

				cmake.append("-DFFTW3_INCLUDE_DIR=%s/fftw-3.3.4/include" % libs_prefix)
				cmake.append("-DFFTW3_LIBRARY=%s/fftw-3.3.4/lib/libfftw3.a" % libs_prefix)

				cmake.append("-DBoost_DIR=%s/boost" % libs_prefix)
				cmake.append("-DBoost_INCLUDE_DIR=%s/boost/include" % libs_prefix)
				cmake.append("-DBoost_LIBRARY_DIRS=%s/boost/lib" % libs_prefix)
				cmake.append("-DBoost_DATE_TIME_LIBRARY=%s/boost/lib/libboost_date_time.a" % libs_prefix)
				cmake.append("-DBoost_DATE_TIME_LIBRARY_RELEASE=%s/boost/lib/libboost_date_time.a" % libs_prefix)
				cmake.append("-DBoost_FILESYSTEM_LIBRARY=%s/boost/lib/libboost_filesystem.a" % libs_prefix)
				cmake.append("-DBoost_FILESYSTEM_LIBRARY_RELEASE=%s/boost/lib/libboost_filesystem.a" % libs_prefix)
				cmake.append("-DBoost_REGEX_LIBRARY=%s/boost/lib/libboost_regex.a" % libs_prefix)
				cmake.append("-DBoost_REGEX_LIBRARY_RELEASE=%s/boost/lib/libboost_regex.a" % libs_prefix)
				cmake.append("-DBoost_SYSTEM_LIBRARY=%s/boost/lib/libboost_system.a" % libs_prefix)
				cmake.append("-DBoost_SYSTEM_LIBRARY_RELEASE=%s/boost/lib/libboost_system.a" % libs_prefix)
				cmake.append("-DBoost_THREAD_LIBRARY=%s/boost/lib/libboost_thread.a" % libs_prefix)
				cmake.append("-DBoost_THREAD_LIBRARY_RELEASE=%s/boost/lib/libboost_thread.a" % libs_prefix)
				cmake.append("-DBoost_LOCALE_LIBRARY=%s/boost/lib/libboost_locale.a" % libs_prefix)
				cmake.append("-DBoost_LOCALE_LIBRARY_RELEASE=%s/boost/lib/libboost_locale.a" % libs_prefix)

				cmake.append("-DOPENEXR_HALF_LIBRARY=%s/openexr/lib/libHalf.a" % libs_prefix)
				cmake.append("-DOPENEXR_IEX_LIBRARY=%s/openexr/lib/libIex.a" % libs_prefix)
				cmake.append("-DOPENEXR_ILMIMF_LIBRARY=%s/openexr/lib/libIlmImf.a" % libs_prefix)
				cmake.append("-DOPENEXR_ILMTHREAD_LIBRARY=%s/openexr/lib/libIlmThread.a" % libs_prefix)
				cmake.append("-DOPENEXR_IMATH_LIBRARY=%s/openexr/lib/libImath.a" % libs_prefix)
				cmake.append("-DOPENEXR_INCLUDE_DIR=%s/openexr/include" % libs_prefix)

				cmake.append("-DOPENCOLORIO_INCLUDE_DIR=%s/ocio/include" % libs_prefix)
				cmake.append("-DOPENCOLORIO_TINYXML_LIBRARY=%s/ocio/lib/libtinyxml.a" % libs_prefix)
				cmake.append("-DOPENCOLORIO_YAML-CPP_LIBRARY=%s/ocio/lib/libyaml-cpp.a" % libs_prefix)
				cmake.append("-D_opencolorio_LIBRARIES=%s/ocio/lib/libOpenColorIO.a" % libs_prefix)

				cmake.append("-DOPENIMAGEIO_INCLUDE_DIR=%s/oiio/include/" % libs_prefix)
				cmake.append("-DOPENIMAGEIO_LIBRARY=%s/oiio/lib/libOpenImageIO.a" % libs_prefix)

				cmake.append("-DPYTHON_VERSION=%s" % PYTHON_VERSION_BIG)
				cmake.append("-DPYTHON_ROOT_DIR=%s/python-%s" % (libs_prefix, PYTHON_VERSION_BIG))
				cmake.append("-DPYTHON_LIBRARY=%s/python-%s/lib/libpython%sm.a" % (libs_prefix, PYTHON_VERSION_BIG, PYTHON_VERSION_BIG))
				cmake.append("-DPYTHON_LIBPATH=%s/python-%s/lib" % (libs_prefix, PYTHON_VERSION_BIG))
				cmake.append("-DPYTHON_LIBRARIES=%s/python-%s/lib" % (libs_prefix, PYTHON_VERSION_BIG))
				cmake.append("-DPYTHON_INCLUDE_DIR=%s/python-%s/include/python%sm" % (libs_prefix, PYTHON_VERSION_BIG, PYTHON_VERSION_BIG))
				cmake.append("-DPYTHON_INCLUDE_CONFIG_DIR=%s/python-%s/include/python%sm" % (libs_prefix, PYTHON_VERSION_BIG, PYTHON_VERSION_BIG))
				cmake.append("-DPYTHON_NUMPY_PATH=%s" % libs_prefix) # cmake will append numpy to path 

				cmake.append("-DTIFF_INCLUDE_DIR=%s/tiff/include" % libs_prefix)
				cmake.append("-DTIFF_LIBRARY=%s/tiff/lib/libtiff.a" % libs_prefix)

				cmake.append("-DLLVM_ROOT_DIR=%s/llvm-%s" % (libs_prefix, LLVM_VERSION))
				cmake.append("-DFFMPEG_ROOT_DIR=%s/ffmpeg" % libs_prefix)

				cmake.append("-DOSL_ROOT_DIR=%s/osl-%s" % (libs_prefix, OSL_VERSION))
				cmake.append("-DOSL_ROOT=%s/osl-%s" % (libs_prefix, OSL_VERSION))
				cmake.append("-DOSL_INCLUDE_DIR=%s/osl-%s/include" % (libs_prefix, OSL_VERSION))

				cmake.append("-DGIFLIB_LIBRARY=%s/giflib-%s/lib/libgif.a" % (libs_prefix, GIFLIB_VERSION))
				cmake.append("-DWEBP_LIBRARY=%s/webp-%s/lib/libwebp.a" % (libs_prefix, WEBP_VERSION))
				cmake.append("-DOPENCOLLADA_ROOT_DIR=%s" % getLibPath('collada'))

				cmake.append("-DPCRE_ROOT_DIR=%s" % getLibPath('pcre'))
			else:
				cmake.append("-DBoost_DIR=%s/boost" % libs_prefix)
				cmake.append("-DBoost_INCLUDE_DIR=%s/boost/include" % libs_prefix)
				cmake.append("-DBoost_LIBRARY_DIRS=%s/boost/lib" % libs_prefix)
				cmake.append("-DBoost_DATE_TIME_LIBRARY=%s/boost/lib/libboost_date_time.a" % libs_prefix)
				cmake.append("-DBoost_DATE_TIME_LIBRARY_DEBUG=%s/boost/lib/libboost_date_time.a" % libs_prefix)
				cmake.append("-DBoost_DATE_TIME_LIBRARY_RELEASE=%s/boost/lib/libboost_date_time.a" % libs_prefix)
				cmake.append("-DBoost_FILESYSTEM_LIBRARY=%s/boost/lib/libboost_filesystem.a" % libs_prefix)
				cmake.append("-DBoost_FILESYSTEM_LIBRARY_DEBUG=%s/boost/lib/libboost_filesystem.a" % libs_prefix)
				cmake.append("-DBoost_FILESYSTEM_LIBRARY_RELEASE=%s/boost/lib/libboost_filesystem.a" % libs_prefix)
				cmake.append("-DBoost_REGEX_LIBRARY=%s/boost/lib/libboost_regex.a" % libs_prefix)
				cmake.append("-DBoost_REGEX_LIBRARY_DEBUG=%s/boost/lib/libboost_regex.a" % libs_prefix)
				cmake.append("-DBoost_REGEX_LIBRARY_RELEASE=%s/boost/lib/libboost_regex.a" % libs_prefix)
				cmake.append("-DBoost_SYSTEM_LIBRARY=%s/boost/lib/libboost_system.a" % libs_prefix)
				cmake.append("-DBoost_SYSTEM_LIBRARY_DEBUG=%s/boost/lib/libboost_system.a" % libs_prefix)
				cmake.append("-DBoost_SYSTEM_LIBRARY_RELEASE=%s/boost/lib/libboost_system.a" % libs_prefix)
				cmake.append("-DBoost_THREAD_LIBRARY=%s/boost/lib/libboost_thread.a" % libs_prefix)
				cmake.append("-DBoost_THREAD_LIBRARY_DEBUG=%s/boost/lib/libboost_thread.a" % libs_prefix)
				cmake.append("-DBoost_THREAD_LIBRARY_RELEASE=%s/boost/lib/libboost_thread.a" % libs_prefix)
				cmake.append("-DBoost_LOCALE_LIBRARY=%s/boost/lib/libboost_locale.a" % libs_prefix)
				cmake.append("-DBoost_LOCALE_LIBRARY_DEBUG=%s/boost/lib/libboost_locale.a" % libs_prefix)
				cmake.append("-DBoost_LOCALE_LIBRARY_RELEASE=%s/boost/lib/libboost_locale.a" % libs_prefix)
				cmake.append("-DOPENEXR_ROOT_DIR=%s/openexr" % libs_prefix)
				cmake.append("-DOPENEXR_ILMIMF_LIBRARY=%s/openexr/lib/libIlmImf.a" % libs_prefix)

				cmake.append("-D_opencolorio_LIBRARIES=%s/ocio/lib/libOpenColorIO.a" % libs_prefix)
				cmake.append("-DOPENCOLORIO_INCLUDE_DIR=%s/ocio/include" % libs_prefix)
				cmake.append("-DOPENCOLORIO_TINYXML_LIBRARY=%s/ocio/lib/libtinyxml.a" % libs_prefix)
				cmake.append("-DOPENCOLORIO_YAML-CPP_LIBRARY=%s/ocio/lib/libyaml-cpp.a" % libs_prefix)

				cmake.append("-DOPENIMAGEIO_INCLUDE_DIR=%s/oiio/include/" % libs_prefix)
				cmake.append("-DOPENIMAGEIO_LIBRARY=%s/oiio/lib/libOpenImageIO.a" % libs_prefix)

				cmake.append("-DPYTHON_VERSION=%s" % PYTHON_VERSION_BIG)
				cmake.append("-DPYTHON_ROOT_DIR=%s/python-%s" % (libs_prefix, PYTHON_VERSION_BIG))
				cmake.append("-DPYTHON_LIBRARY=%s/python-%s/lib/libpython%sm.a" % (libs_prefix, PYTHON_VERSION_BIG, PYTHON_VERSION_BIG))
				cmake.append("-DPYTHON_LIBPATH=%s/python-%s/lib" % (libs_prefix, PYTHON_VERSION_BIG))
				cmake.append("-DPYTHON_LIBRARIES=%s/python-%s/lib" % (libs_prefix, PYTHON_VERSION_BIG))
				cmake.append("-DPYTHON_INCLUDE_DIR=%s/python-%s/include/python%sm" % (libs_prefix, PYTHON_VERSION_BIG, PYTHON_VERSION_BIG))
				cmake.append("-DPYTHON_INCLUDE_CONFIG_DIR=%s/python-%s/include/python%sm" % (libs_prefix, PYTHON_VERSION_BIG, PYTHON_VERSION_BIG))
				cmake.append("-DPYTHON_NUMPY_PATH=%s" %  libs_prefix) # cmake will append numpy to path 

		if self.jenkins:
			cmake.append("-DJPEG_LIBRARY=%s" % os.path.join(self.dir_source, 'blender-for-vray-libs', 'Linux', 'jpeg-turbo', 'lib', 'Release', 'libjpeg-turbo.a'))
			cmake.append("-DJPEG_INCLUDE_DIR=%s" % os.path.join(self.dir_source, 'blender-for-vray-libs', 'Linux', 'jpeg-turbo', 'include'))

		cmake.append(self.dir_blender)

		sys.stdout.write('cmake args:\n%s\n' % '\n\t'.join(cmake))
		sys.stdout.flush()

		if not self.mode_test:
			res = subprocess.call(cmake)
			if not res == 0:
				sys.stderr.write("There was an error during configuration!\n")
				sys.exit(1)

			self.write_buildinfo(cmake_build_dir)

			make = ['ninja']
			make.append('-j%s' % self.build_jobs)
			make.append('install')

			res = subprocess.call(make)
			if not res == 0:
				sys.stderr.write("There was an error during the compilation!\n")
				sys.exit(1)


	def package(self):
		subdir = "linux" + "/" + self.build_arch

		release_path = os.path.join(self.dir_release, subdir)
		if self.jenkins:
			utils.WritePackageInfo(self, release_path)

		if not self.mode_test:
			utils.path_create(release_path)

		installer_name = utils.GetPackageName(self)
		archive_name = utils.GetPackageName(self, ext='tar.bz2')
		installer_path = utils.path_slashify(utils.path_join(release_path, installer_name))
		installer_root = utils.path_join(self.dir_source, "vb25-patch", "installer")

		sys.stdout.write("Generating installer: %s\n" % (installer_path))
		utils.GenCGRInstaller(self, installer_path, InstallerDir=self.dir_cgr_installer)

		cmd = "tar jcf %s %s" % (archive_name, installer_name)

		sys.stdout.write(cmd)
		sys.stdout.flush()

		if not self.mode_test:
			os.chdir(release_path)
			res = subprocess.call(cmd, shell=True)
			if res != 0:
				sys.stderr.write('Failed to archive installer bin')
				sys.stderr.flush()
				sys.exit(1)

		artefacts = (
			os.path.join(release_path, installer_name),
			os.path.join(release_path, archive_name),
		)

		sys.stdout.write("##teamcity[setParameter name='env.ENV_ARTEFACT_FILES' value='%s']" % '|n'.join(artefacts))
		sys.stdout.flush()

		return subdir, archive_name
