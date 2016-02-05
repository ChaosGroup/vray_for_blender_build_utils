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
import shutil
import subprocess
import inspect

from .builder import utils
from .builder import Builder


def getDepsCompilationData(prefix, wd, jobs):
	PYTHON_VERSION="3.5.1"
	PYTHON_VERSION_BIG="3.5"
	NUMPY_VERSION="1.10.1"
	BOOST_VERSION="1.60.0"
	OCIO_VERSION="1.0.9"
	OPENEXR_VERSION="2.2.0"
	ILMBASE_VERSION="2.2.0"
	OIIO_VERSION="1.6.9"
	LLVM_VERSION="3.4"

	def dbg(x):
		sys.stdout.write(x)
		sys.stdout.write("")
		return True

	def getChDirCmd(newDir):
		return lambda: os.chdir(newDir) or True

	def getDownloadCmd(url, name):
		return lambda: dbg('wget -c %s -O %s/%s' % (url, wd, name)) and 0 == os.system('wget -c %s -O %s/%s' % (url, wd, name))

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

	steps = (
		('python', '%s/python-%s' % (prefix, PYTHON_VERSION), (
			getChDirCmd(wd),
			getDownloadCmd("https://www.python.org/ftp/python/%s/Python-%s.tgz" % (PYTHON_VERSION, PYTHON_VERSION), 'python.tgz'),
			'tar -C . -xf python.tgz',
			getChDirCmd(os.path.join(wd, 'Python-%s' % PYTHON_VERSION)),
			'./configure --prefix=%s/python-%s --libdir=%s/python-%s/lib --enable-ipv6 --enable-loadable-sqlite-extensions --with-dbmliborder=bdb --with-computed-gotos --with-pymalloc'
				% (prefix, PYTHON_VERSION, prefix, PYTHON_VERSION),
			'make -j %s' % jobs,
			'make install',
			'ln -s %s/python-%s %s/python' % (prefix, PYTHON_VERSION, prefix),
		)),
		('numpy', '%s/numpy-%s' % (prefix, NUMPY_VERSION), (
			getChDirCmd(wd),
			getDownloadCmd("http://sourceforge.net/projects/numpy/files/NumPy/%s/numpy-%s.tar.gz" % (NUMPY_VERSION, NUMPY_VERSION), 'numpy.tar.gz'),
			'tar -C . -xf numpy.tar.gz',
			getChDirCmd(os.path.join(wd, 'numpy-%s' % NUMPY_VERSION)),
			'%s/python/bin/python3 setup.py install --prefix=%s/numpy-%s' % (prefix, prefix, NUMPY_VERSION),
			'ln -s %s/numpy-%s %s/python/lib/python%s/site-packages/numpy' % (prefix, NUMPY_VERSION, prefix, PYTHON_VERSION_BIG)
		)),
		('boost', '%s/boost-%s' % (prefix, BOOST_VERSION),(
			getChDirCmd(wd),
			getDownloadCmd("http://sourceforge.net/projects/boost/files/boost/%s/boost_%s.tar.bz2/download" % (BOOST_VERSION, BOOST_VERSION.replace('.', '_')), 'boost.tar.bz2'),
			'tar -C . --transform "s,(.*/?)boost_1_[^/]+(.*),\\1boost-%s\\2,x" -xf boost.tar.bz2' % BOOST_VERSION,
			getChDirCmd(os.path.join(wd, 'boost-%s' % BOOST_VERSION)),
			'./bootstrap.sh',
			'./b2 -j 4 -a --with-system --with-filesystem --with-thread --with-regex --with-locale --with-date_time --with-wave --prefix=%s/boost-%s --disable-icu boost.locale.icu=off install'
				% (prefix, BOOST_VERSION),
			'./b2 clean',
			'ln -s %s/boost-%s %s/boost' % (prefix, BOOST_VERSION, prefix),
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
		)),
		('oiio', '%s/oiio-%s' % (prefix, OIIO_VERSION), (
			getChDirCmd(wd),
			getDownloadCmd("https://github.com/OpenImageIO/oiio/archive/Release-%s.tar.gz" % OIIO_VERSION, 'oiio.tar.gz'),
			'mkdir -p OpenImageIO-%s' % OIIO_VERSION,
			'tar -C OpenImageIO-%s --strip-components=1 --transform "s,(.*/?)oiio-Release-[^/]*(.*),\\1OpenImageIO-%s\\2,x" -xf oiio.tar.gz'
				% (OIIO_VERSION, OIIO_VERSION),
			'mkdir -p OpenImageIO-%s/build' % OIIO_VERSION,
			getChDirCmd(os.path.join(wd, 'OpenImageIO-%s' % OIIO_VERSION, 'build')),
			' '.join(
				["cmake", "-D CMAKE_BUILD_TYPE=Release", "-D CMAKE_PREFIX_PATH=%s" % prefix,
				 "-D CMAKE_INSTALL_PREFIX=%s/oiio-%s" % (prefix, OIIO_VERSION),
				 "-D STOP_ON_WARNING=OFF", "-D BUILDSTATIC=ON", "-D LINKSTATIC=ON", "-D USE_QT=OFF", "-D USE_PYTHON=OFF",
				 "-D BUILD_TESTING=OFF", "-D OIIO_BUILD_TESTS=OFF", "-D OIIO_BUILD_TOOLS=OFF",
				 "-D ILMBASE_VERSION=%s" % ILMBASE_VERSION ,"-D OPENEXR_VERSION=%s" % OPENEXR_VERSION,
				 "-D ILMBASE_HOME=%s/openexr" % prefix, "-D OPENEXR_HOME=%s/openexr" % prefix,
				 "-D BOOST_ROOT=%s/boost" % prefix, "-D Boost_NO_SYSTEM_PATHS=ON", "-D USE_OCIO=OFF",
				 "-D CMAKE_CXX_FLAGS=\"-fPIC\"", "-D CMAKE_EXE_LINKER_FLAGS=\"-lgcc_s -lgcc\"", ".."]),
			'make -j %s' % jobs,
			'make install',
			'make clean',
			'ln -s %s/oiio-%s %s/oiio' % (prefix, OIIO_VERSION, prefix),
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
	)

	return steps


Deps = {
	'ubuntu': {
		'cmd' : "apt-get install",
		'packages' : (
			'build-essential',
			'libalut-dev',
			'libavcodec-dev',
			'libavdevice-dev',
			'libavformat-dev',
			'libavutil-dev',
			'libfftw3-dev',
			'libfreetype6-dev',
			'libglew-dev',
			'libcheese-dev', # Fixes libglew-dev installation
			'libglu1-mesa-dev',
			'libjack-dev',
			'libjack-dev',
			'libjpeg-dev',
			'libmp3lame-dev',
			'libopenal-dev',
			'libopenexr-dev',
			'libopenjpeg-dev',
			'libpng12-dev',
			'libsdl1.2-dev',
			'libsndfile1-dev',
			'libspnav-dev',
			'libswscale-dev',
			'libtheora-dev',
			'libtiff4-dev',
			'libvorbis-dev',
			'libx264-dev',
			'libxi-dev',
			'python3.4-dev',
			'python3-numpy',
			'libopenimageio-dev',
			'libopencolorio-dev',
			'libboost-all-dev'
		)
	},
}


def DepsInstall(self):
	sys.stdout.write("Installing dependencies: \n")

	distr = utils.get_linux_distribution()['short_name']

	if distr in Deps:
		cmd = "sudo %s %s" % (
			Deps[distr]['cmd'],
			" ".join(Deps[distr]['packages'])
		)
		sys.stdout.write("Calling: %s\n" % cmd)
		os.system(cmd)

	else:
		sys.stdout.write("Your distribution \"%s\" doesn't support automatic dependencies installation!\n" % distr)


def DepsBuild(self):
	# if not self.with_osl:
	# 	cmd += " --skip-llvm"
	# 	cmd += " --skip-osl"

	# if self.with_collada:
	# 	cmd += " --with-opencollada"
	# else:
	# 	cmd += " --skip-opencollada"
	wd = '/root/src'
	os.makedirs(wd)
	prefix = '/opt/lib' if utils.get_linux_distribution()['short_name'] == 'centos' else '/opt'

	data = getDepsCompilationData(prefix, wd, self.build_jobs)

	if self.mode_test:
		# TODO: print out commands
		return

	for item in data:
		sys.stdout.write('Installing %s...' % item[0])
		shouldStop = False
		if os.path.isdir(item[1]):
			# we already have this lib
			continue

		for step in item[2]:
			sys.stdout.write("CWD %s" % os.getcwd())
			if callable(step):
				sys.stdout.write('Callable step: \n\t%s\n' % inspect.getsource(step).strip())
				if not step():
					sys.stdout.write('Failed! Stopping...')
					shouldStop = True
					break
				sys.stdout.write('')
			else:
				sys.stdout.write('Command step: \n\t%s\n' % step)
				res = subprocess.call(step, shell=True)
				if res != 0:
					sys.stdout.write('Failed! Stopping...')
					shouldStop = True
					break;
		if shouldStop:
			break


class LinuxBuilder(Builder):
	def post_init(self):
		if utils.get_host_os() == utils.LNX:
			DepsBuild(self)

	def compile(self):
		cmake_build_dir = os.path.join(self.dir_source, "blender-cmake-build")
		if self.build_clean and os.path.exists(cmake_build_dir):
			utils.remove_directory(cmake_build_dir)
		if not os.path.exists(cmake_build_dir):
			os.makedirs(cmake_build_dir)
		os.chdir(cmake_build_dir)

		PYTHON_VERSION = "3.5"

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

		cmake.append("-DWITH_VRAY_FOR_BLENDER=ON")
		cmake.append("-DUSE_BLENDER_VRAY_ZMQ=ON")
		cmake.append("-DLIBS_ROOT=%s" % utils.path_join(self.dir_source, 'blender-for-vray-libs'))

		cmake.append("-DWITH_GAMEENGINE=%s" % utils.GetCmakeOnOff(self.with_ge))
		cmake.append("-DWITH_PLAYER=%s" % utils.GetCmakeOnOff(self.with_player))
		cmake.append("-DWITH_LIBMV=%s" % utils.GetCmakeOnOff(self.with_tracker))
		cmake.append("-DWITH_OPENCOLLADA=%s" % utils.GetCmakeOnOff(self.with_collada))
		cmake.append("-DWITH_CYCLES=%s" % utils.GetCmakeOnOff(self.with_cycles))
		cmake.append("-DWITH_MOD_OCEANSIM=ON")
		cmake.append("-DWITH_OPENSUBDIV=ON")

		if self.dev_static_libs:
			if distr_info['short_name'] == 'centos':

				# NOTES:
				#   OpenJPEG is disabled in OpenImageIO
				#   Smth wrong with OpenAL headers - disabling
				#
				cmake.append("-DWITH_OPENAL=OFF")

				cmake.append("-DFFTW3_INCLUDE_DIR=/opt/lib/fftw-3.3.4/include")
				cmake.append("-DFFTW3_LIBRARY=/opt/lib/fftw-3.3.4/lib/libfftw3.a")

				cmake.append("-DBoost_DIR=/opt/lib/boost")
				cmake.append("-DBoost_INCLUDE_DIR=/opt/lib/boost/include")
				cmake.append("-DBoost_LIBRARY_DIRS=/opt/lib/boost/lib")
				cmake.append("-DBoost_DATE_TIME_LIBRARY=/opt/lib/boost/lib/libboost_date_time.a")
				cmake.append("-DBoost_DATE_TIME_LIBRARY_RELEASE=/opt/lib/boost/lib/libboost_date_time.a")
				cmake.append("-DBoost_FILESYSTEM_LIBRARY=/opt/lib/boost/lib/libboost_filesystem.a")
				cmake.append("-DBoost_FILESYSTEM_LIBRARY_RELEASE=/opt/lib/boost/lib/libboost_filesystem.a")
				cmake.append("-DBoost_REGEX_LIBRARY=/opt/lib/boost/lib/libboost_regex.a")
				cmake.append("-DBoost_REGEX_LIBRARY_RELEASE=/opt/lib/boost/lib/libboost_regex.a")
				cmake.append("-DBoost_SYSTEM_LIBRARY=/opt/lib/boost/lib/libboost_system.a")
				cmake.append("-DBoost_SYSTEM_LIBRARY_RELEASE=/opt/lib/boost/lib/libboost_system.a")
				cmake.append("-DBoost_THREAD_LIBRARY=/opt/lib/boost/lib/libboost_thread.a")
				cmake.append("-DBoost_THREAD_LIBRARY_RELEASE=/opt/lib/boost/lib/libboost_thread.a")
				cmake.append("-DBoost_LOCALE_LIBRARY=/opt/lib/boost/lib/libboost_locale.a")
				cmake.append("-DBoost_LOCALE_LIBRARY_RELEASE=/opt/lib/boost/lib/libboost_locale.a")

				cmake.append("-DOPENEXR_HALF_LIBRARY=/opt/lib/openexr/lib/libHalf.a")
				cmake.append("-DOPENEXR_IEX_LIBRARY=/opt/lib/openexr/lib/libIex.a")
				cmake.append("-DOPENEXR_ILMIMF_LIBRARY=/opt/lib/openexr/lib/libIlmImf.a")
				cmake.append("-DOPENEXR_ILMTHREAD_LIBRARY=/opt/lib/openexr/lib/libIlmThread.a")
				cmake.append("-DOPENEXR_IMATH_LIBRARY=/opt/lib/openexr/lib/libImath.a")
				cmake.append("-DOPENEXR_INCLUDE_DIR=/opt/lib/openexr/include")

				cmake.append("-DOPENCOLORIO_INCLUDE_DIR=/opt/lib/ocio/include")
				cmake.append("-DOPENCOLORIO_TINYXML_LIBRARY=/opt/lib/ocio/lib/libtinyxml.a")
				cmake.append("-DOPENCOLORIO_YAML-CPP_LIBRARY=/opt/lib/ocio/lib/libyaml-cpp.a")
				cmake.append("-D_opencolorio_LIBRARIES=/opt/lib/ocio/lib/libOpenColorIO.a")

				cmake.append("-DOPENIMAGEIO_INCLUDE_DIR=/opt/lib/oiio/include/")
				cmake.append("-DOPENIMAGEIO_LIBRARY=/opt/lib/oiio/lib/libOpenImageIO.a")

				cmake.append("-DPYTHON_VERSION=%s" % PYTHON_VERSION)
				cmake.append("-DPYTHON_ROOT_DIR=/opt/lib/python-%s" % PYTHON_VERSION)
				cmake.append("-DPYTHON_LIBRARY=/opt/lib/python-%s/lib/libpython%sm.a" % (PYTHON_VERSION, PYTHON_VERSION))
				cmake.append("-DPYTHON_LIBPATH=/opt/lib/python-%s/lib" % PYTHON_VERSION)
				cmake.append("-DPYTHON_LIBRARIES=/opt/lib/python-%s/lib" % PYTHON_VERSION)
				cmake.append("-DPYTHON_INCLUDE_DIR=/opt/lib/python-%s/include/python%sm" % (PYTHON_VERSION, PYTHON_VERSION))
				cmake.append("-DPYTHON_INCLUDE_CONFIG_DIR=/opt/lib/python-%s/include/python%sm" % (PYTHON_VERSION, PYTHON_VERSION))
				cmake.append("-DPYTHON_NUMPY_PATH=/opt/lib/python-%s/lib/python%s/site-packages" % (PYTHON_VERSION, PYTHON_VERSION))

				cmake.append("-DTIFF_INCLUDE_DIR=/opt/lib/tiff-3.9.7/include")
				cmake.append("-DTIFF_LIBRARY=/opt/lib/tiff-3.9.7/lib/libtiff.a")

			else:
				cmake.append("-DBoost_DIR=/opt/boost")
				cmake.append("-DBoost_INCLUDE_DIR=/opt/boost/include")
				cmake.append("-DBoost_LIBRARY_DIRS=/opt/boost/lib")
				cmake.append("-DBoost_DATE_TIME_LIBRARY=/opt/boost/lib/libboost_date_time.a")
				cmake.append("-DBoost_DATE_TIME_LIBRARY_DEBUG=/opt/boost/lib/libboost_date_time.a")
				cmake.append("-DBoost_DATE_TIME_LIBRARY_RELEASE=/opt/boost/lib/libboost_date_time.a")
				cmake.append("-DBoost_FILESYSTEM_LIBRARY=/opt/boost/lib/libboost_filesystem.a")
				cmake.append("-DBoost_FILESYSTEM_LIBRARY_DEBUG=/opt/boost/lib/libboost_filesystem.a")
				cmake.append("-DBoost_FILESYSTEM_LIBRARY_RELEASE=/opt/boost/lib/libboost_filesystem.a")
				cmake.append("-DBoost_REGEX_LIBRARY=/opt/boost/lib/libboost_regex.a")
				cmake.append("-DBoost_REGEX_LIBRARY_DEBUG=/opt/boost/lib/libboost_regex.a")
				cmake.append("-DBoost_REGEX_LIBRARY_RELEASE=/opt/boost/lib/libboost_regex.a")
				cmake.append("-DBoost_SYSTEM_LIBRARY=/opt/boost/lib/libboost_system.a")
				cmake.append("-DBoost_SYSTEM_LIBRARY_DEBUG=/opt/boost/lib/libboost_system.a")
				cmake.append("-DBoost_SYSTEM_LIBRARY_RELEASE=/opt/boost/lib/libboost_system.a")
				cmake.append("-DBoost_THREAD_LIBRARY=/opt/boost/lib/libboost_thread.a")
				cmake.append("-DBoost_THREAD_LIBRARY_DEBUG=/opt/boost/lib/libboost_thread.a")
				cmake.append("-DBoost_THREAD_LIBRARY_RELEASE=/opt/boost/lib/libboost_thread.a")
				cmake.append("-DBoost_LOCALE_LIBRARY=/opt/boost/lib/libboost_locale.a")
				cmake.append("-DBoost_LOCALE_LIBRARY_DEBUG=/opt/boost/lib/libboost_locale.a")
				cmake.append("-DBoost_LOCALE_LIBRARY_RELEASE=/opt/boost/lib/libboost_locale.a")
				cmake.append("-DOPENEXR_ROOT_DIR=/opt/openexr")
				cmake.append("-DOPENEXR_ILMIMF_LIBRARY=/opt/openexr/lib/libIlmImf-2_1.a")
				cmake.append("-D_opencolorio_LIBRARIES=/opt/ocio/lib/libOpenColorIO.a")
				cmake.append("-DOPENCOLORIO_INCLUDE_DIR=/opt/ocio/include")
				cmake.append("-DOPENCOLORIO_TINYXML_LIBRARY=/opt/ocio/lib/libtinyxml.a")
				cmake.append("-DOPENCOLORIO_YAML-CPP_LIBRARY=/opt/ocio/lib/libyaml-cpp.a")
				cmake.append("-DOPENIMAGEIO_INCLUDE_DIR=/opt/oiio/include/")
				cmake.append("-DOPENIMAGEIO_LIBRARY=/opt/oiio/lib/libOpenImageIO.a")
				cmake.append("-DPYTHON_VERSION=3.4")
				cmake.append("-DPYTHON_ROOT_DIR=/opt/python-3.3")
				cmake.append("-DPYTHON_LIBRARY=/opt/python-3.3/lib/libpython3.4m.a")
				cmake.append("-DPYTHON_LIBPATH=/opt/python-3.3/lib")
				cmake.append("-DPYTHON_LIBRARIES=/opt/python-3.3/lib")
				cmake.append("-DPYTHON_INCLUDE_DIR=/opt/python-3.3/include/python3.4m")
				cmake.append("-DPYTHON_INCLUDE_CONFIG_DIR=/opt/python-3.3/include/python3.4m")
				cmake.append("-DPYTHON_NUMPY_PATH=/opt/python-3.3/lib/python3.4/site-packages")

		cmake.append("-DCMAKE_MAKE_PROGRAM=ninja")
		cmake.append("-DCMAKE_C_COMPILER_ENV_VAR=CC")
		cmake.append("-DCMAKE_CXX_COMPILER_ENV_VAR=CXX")
		cmake.append("../blender")

		if self.mode_test:
			print(" ".join(cmake))

		else:
			res = subprocess.call(cmake)
			if not res == 0:
				sys.stderr.write("There was an error during configuration!\n")
				sys.exit(1)

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

		if not self.mode_test:
			utils.path_create(release_path)

		archive_name = utils.GetPackageName(self)
		archive_path = utils.path_join(release_path, archive_name)

		sys.stdout.write("Generating archive: %s\n" % (archive_name))
		sys.stdout.write("  in: %s\n" % (release_path))

		installer_name = utils.GetPackageName(self)
		installer_path = utils.path_slashify(utils.path_join(release_path, installer_name))
		installer_root = utils.path_join(self.dir_source, "vb25-patch", "installer")

		utils.GenCGRInstaller(self, installer_path, InstallerDir=self.dir_cgr_installer)
		return subdir, installer_path
