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

PYTHON_VERSION="3.5.1"
PYTHON_VERSION_BIG="3.5"
NUMPY_VERSION="1.10.1"
BOOST_VERSION="1.60.0"
OCIO_VERSION="1.0.9"
OPENEXR_VERSION="2.2.0"
ILMBASE_VERSION="2.2.0"
OIIO_VERSION="1.6.9"
LLVM_VERSION="3.4"
TIFF_VERSION="3.9.7"


def getDepsCompilationData(prefix, wd, jobs):
	def dbg(x):
		sys.stdout.write('%s\n' % x)
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
			'ln -s %s/python-%s %s/python-%s' % (prefix, PYTHON_VERSION, prefix, PYTHON_VERSION_BIG),
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
		('tiff', '%s/tiff-%s' % (prefix, TIFF_VERSION), (
			getChDirCmd(wd),
			getDownloadCmd('http://download.osgeo.org/libtiff/tiff-%s.tar.gz' % TIFF_VERSION, 'tiff.tar.gz'),
			'tar -C . -xf tiff.tar.gz',
			getChDirCmd(os.path.join(wd, 'tiff-%s' % TIFF_VERSION)),
			'./configure --prefix=/opt/tc-libs/tiff-%s --enable-static' % TIFF_VERSION,
			'make -j %s' % jobs,
			'make  install',
			'ln -s %s/tiff-%s %s/tiff' % (prefix, TIFF_VERSION, prefix)
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
	wd = os.path.expanduser('~/blender-libs-builds')
	if not os.path.isdir(wd):
		os.makedirs(wd)

	prefix = '/opt/lib' if utils.get_linux_distribution()['short_name'] == 'centos' else '/opt'
	if self.dir_blender_libs != '':
		prefix = self.dir_blender_libs

	self._blender_libs_location = prefix

	data = getDepsCompilationData(prefix, wd, self.build_jobs)

	if self.mode_test:
		# TODO: print out commands
		return

	sys.stdout.write('Building dependencies...\n')

	for item in data:
		sys.stdout.write('Installing %s...\n' % item[0])
		shouldStop = False
		if os.path.isdir(item[1]):
			sys.stdout.write('%s already installed, skipping ...\n' % item[1])
			# we already have this lib
			continue

		for step in item[2]:
			sys.stdout.write("CWD %s\n" % os.getcwd())
			if callable(step):
				sys.stdout.write('Callable step: \n\t%s\n' % inspect.getsource(step).strip())
				if not step():
					sys.stdout.write('Failed! Stopping...\n')
					sys.exit(1)
				sys.stdout.write('\n')
			else:
				sys.stdout.write('Command step: \n\t%s\n' % step)
				res = subprocess.call(step, shell=True)
				if res != 0:
					sys.stdout.write('Failed! Stopping...\n')
					sys.exit(1)
			sys.stdout.flush()



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

		if self.teamcity_project_type == 'vb35':
			cmake.append("-DUSE_BLENDER_VRAY_ZMQ=ON")
			cmake.append("-DLIBS_ROOT=%s" % utils.path_join(self.dir_source, 'blender-for-vray-libs'))

		cmake.append("-DWITH_GAMEENGINE=%s" % utils.GetCmakeOnOff(self.with_ge))
		cmake.append("-DWITH_PLAYER=%s" % utils.GetCmakeOnOff(self.with_player))
		cmake.append("-DWITH_LIBMV=%s" % utils.GetCmakeOnOff(self.with_tracker))
		cmake.append("-DWITH_OPENCOLLADA=%s" % utils.GetCmakeOnOff(self.with_collada))
		cmake.append("-DWITH_CYCLES=%s" % utils.GetCmakeOnOff(self.with_cycles))
		cmake.append("-DWITH_MOD_OCEANSIM=ON")
		cmake.append("-DWITH_OPENSUBDIV=ON")

		libs_prefix = '/opt/lib' if utils.get_linux_distribution()['short_name'] == 'centos' else '/opt'

		if hasattr(self, '_blender_libs_location'):
			libs_prefix = self._blender_libs_location

		if self.dev_static_libs:
			if distr_info['short_name'] == 'centos':

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

				if self.teamcity_project_type == 'vb35':
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
				cmake.append("-DPYTHON_NUMPY_PATH=%s/python-%s/lib/python%s/site-packages" % (libs_prefix, PYTHON_VERSION_BIG, PYTHON_VERSION_BIG))

				cmake.append("-DTIFF_INCLUDE_DIR=%s/tiff/include" % libs_prefix)
				cmake.append("-DTIFF_LIBRARY=%s/tiff/lib/libtiff.a" % libs_prefix)

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

				if self.teamcity_project_type == 'vb35':
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
				cmake.append("-DPYTHON_NUMPY_PATH=%s/python-%s/lib/python%s/site-packages" % (libs_prefix, PYTHON_VERSION_BIG, PYTHON_VERSION_BIG))

		cmake.append("../blender")

		sys.stdout.write("%s\n" % '\n'.join(cmake))
		sys.stdout.flush()

		if not self.mode_test:
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

		installer_name = utils.GetPackageName(self)
		installer_path = utils.path_slashify(utils.path_join(release_path, installer_name))
		installer_root = utils.path_join(self.dir_source, "vb25-patch", "installer")

		sys.stdout.write("Generating installer: %s\n" % (installer_path))
		utils.GenCGRInstaller(self, installer_path, InstallerDir=self.dir_cgr_installer)

		cmd = "tar jcf %s %s" % (installer_name.replace('.bin', '.tar.bz2'), installer_name)

		sys.stdout.write(cmd)
		sys.stdout.flush()

		if not self.mode_test:
			os.chdir(release_path)
			res = subprocess.call(cmd, shell=True)
			if res != 0:
				sys.stderr.write('Failed to archive installer bin')
				sys.stderr.flush()
				sys.exit(1)

		return subdir, installer_path
