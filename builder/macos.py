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

from .builder import utils
from .builder import Builder

import os
import sys
import glob
import shutil
import subprocess
import inspect

from .builder import utils
from .builder import Builder

from .linux import PYTHON_VERSION
from .linux import PYTHON_VERSION_BIG
from .linux import NUMPY_VERSION
from .linux import BOOST_VERSION
from .linux import OCIO_VERSION
from .linux import OPENEXR_VERSION
from .linux import ILMBASE_VERSION
from .linux import OIIO_VERSION
from .linux import LLVM_VERSION
from .linux import TIFF_VERSION
from .linux import FFTW_VERSION


def getDepsCompilationData(self, prefix, wd, jobs):
	common_cmake_args = []

	def getCmakeCommandStr(*additionalArgs):
		return ' '.join(['cmake'] + common_cmake_args + list(additionalArgs))

	def dbg(x):
		sys.stdout.write('%s\n' % x)
		sys.stdout.flush()
		return True

	def getChDirCmd(newDir):
		return lambda: os.chdir(newDir) or True

	def getDownloadCmd(url, name):
		return lambda: dbg('wget -c %s -O %s/%s' % (url, wd, name)) and 0 == os.system('wget -c "%s" -O %s/%s' % (url, wd, name))

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
		('tiff', '%s/tiff-%s' % (prefix, TIFF_VERSION), (
			getChDirCmd(wd),
			getDownloadCmd('http://download.osgeo.org/libtiff/tiff-%s.tar.gz' % TIFF_VERSION, 'tiff.tar.gz'),
			'tar -C . -xf tiff.tar.gz',
			getChDirCmd(os.path.join(wd, 'tiff-%s' % TIFF_VERSION)),
			'./configure --prefix=%s/tiff-%s --enable-static' % (prefix, TIFF_VERSION),
			'make -j %s' % jobs,
			'make  install',
			'ln -s %s/tiff-%s %s/tiff' % (prefix, TIFF_VERSION, prefix),
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
		)),
		('ocio', '%s/ocio-%s' % (prefix, OCIO_VERSION), (
			getChDirCmd(wd),
			getDownloadCmd("https://github.com/imageworks/OpenColorIO/tarball/v%s" % OCIO_VERSION, 'ocio.tar.gz'),
			'tar -xf ocio.tar.gz',
			'mv imageworks-OpenColorIO* OpenColorIO-%s' % OCIO_VERSION,
			'mkdir -p OpenColorIO-%s/build' % OCIO_VERSION,
			getChDirCmd(os.path.join(wd, 'OpenColorIO-%s' % OCIO_VERSION, 'build')),
			' '.join(["cmake", "-D CMAKE_BUILD_TYPE=Release", "-D CMAKE_PREFIX_PATH=%s/ocio-%s" % (prefix, OCIO_VERSION),
					  "-D CMAKE_INSTALL_PREFIX=%s/ocio-%s" % (prefix, OCIO_VERSION), "-D OCIO_BUILD_APPS=OFF",
					  "-D OCIO_BUILD_PYGLUE=OFF", ".."]),
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
			'tar -xf ilmbase.tar.gz',
			'mv ilmbase-* ILMBase-%s' % ILMBASE_VERSION,
			'mkdir -p ILMBase-%s/build' % ILMBASE_VERSION,
			getChDirCmd(os.path.join(wd, 'ILMBase-%s' % ILMBASE_VERSION, 'build')),
			" ".join(["cmake", "-D CMAKE_BUILD_TYPE=Release", "-D CMAKE_PREFIX_PATH=%s/ilmbase-%s" % (prefix, ILMBASE_VERSION),
					  "-D CMAKE_INSTALL_PREFIX=%s/ilmbase-%s" % (prefix, ILMBASE_VERSION), "-D BUILD_SHARED_LIBS=OFF", ".."]),
			'make -j %s' % jobs,
			'make install',
			'make clean',
		)),
		('openexr', '%s/openexr-%s' % (prefix, OPENEXR_VERSION), (
			getChDirCmd(wd),
			getDownloadCmd("http://download.savannah.nongnu.org/releases/openexr/openexr-%s.tar.gz" % OPENEXR_VERSION, 'openexr.tar.gz'),
			'tar -xf openexr.tar.gz',
			'mv openexr-* OpenEXR-%s' % OPENEXR_VERSION,
			'mkdir -p OpenEXR-%s/build' % OPENEXR_VERSION,
			patchOpenEXRCmake,
			getChDirCmd(os.path.join(wd, 'OpenEXR-%s' % OPENEXR_VERSION, 'build')),
			' '.join(["cmake" , "-D CMAKE_BUILD_TYPE=Release", "-D CMAKE_PREFIX_PATH=%s/openexr-%s" % (prefix, OPENEXR_VERSION),
					  "-D CMAKE_INSTALL_PREFIX=%s/openexr-%s" % (prefix, OPENEXR_VERSION),
					  "-D ILMBASE_PACKAGE_PREFIX=%s/ilmbase-%s" % (prefix, ILMBASE_VERSION), "-D BUILD_SHARED_LIBS=OFF",  ".."]),
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
			'tar -xf oiio.tar.gz',
			'mv oiio-* OpenImageIO-%s' % OIIO_VERSION,
			'mkdir -p OpenImageIO-%s/build' % OIIO_VERSION,
			getChDirCmd(os.path.join(wd, 'OpenImageIO-%s' % OIIO_VERSION, 'build')),
			getCmakeCommandStr(
				"-D CMAKE_BUILD_TYPE=Release", "-D CMAKE_PREFIX_PATH=%s" % prefix,
				"-D CMAKE_INSTALL_PREFIX=%s/oiio-%s" % (prefix, OIIO_VERSION),
				"-D STOP_ON_WARNING=OFF", "-D BUILDSTATIC=ON", "-D LINKSTATIC=ON", "-D USE_QT=OFF", "-D USE_PYTHON=OFF",
				"-D BUILD_TESTING=OFF", "-D OIIO_BUILD_TESTS=OFF", "-D OIIO_BUILD_TOOLS=OFF",
				"-D ILMBASE_VERSION=%s" % ILMBASE_VERSION ,"-D OPENEXR_VERSION=%s" % OPENEXR_VERSION,
				"-D ILMBASE_HOME=%s/openexr" % prefix, "-D OPENEXR_HOME=%s/openexr" % prefix,
				"-D BOOST_ROOT=%s/lib/darwin-9.x.universal/boost" % self.dir_source, "-D Boost_NO_SYSTEM_PATHS=ON", "-D USE_OCIO=OFF", ".."
			),
			'make -j %s' % jobs,
			'make install',
			'make clean',
			'ln -s %s/oiio-%s %s/oiio' % (prefix, OIIO_VERSION, prefix),
		)),
		# ('clang', '%s/llvm-%s' % (prefix, LLVM_VERSION), (
		# 	getChDirCmd(wd),
		# 	getDownloadCmd("http://llvm.org/releases/%s/llvm-%s.src.tar.gz" % (LLVM_VERSION, LLVM_VERSION), 'llvm.tar.gz'),
		# 	getOrCmd(
		# 		getDownloadCmd("http://llvm.org/releases/%s/clang-%s.src.tar.gz" % (LLVM_VERSION, LLVM_VERSION), 'clang.tar.gz'),
		# 		getDownloadCmd("http://llvm.org/releases/%s/cfe-%s.src.tar.gz" % (LLVM_VERSION, LLVM_VERSION), 'clang.tar.gz')
		# 	),
		# 	'tar -C . --transform "s,([^/]*/?)llvm-[^/]*(.*),\\1LLVM-%s\\2,x" -xf llvm.tar.gz' % LLVM_VERSION,
		# 	'tar -C LLVM-%s/tools --transform "s,([^/]*/?)(clang|cfe)-[^/]*(.*),\\1clang\\3,x" -xf clang.tar.gz' % LLVM_VERSION,
		# 	'mkdir -p LLVM-%s/build' % LLVM_VERSION,
		# 	getChDirCmd(os.path.join(wd, 'LLVM-%s' % LLVM_VERSION, 'build')),
		# 	patchLLVMCmake,
		# 	' '.join(["cmake", "-D CMAKE_BUILD_TYPE=Release",
		# 			  "-D CMAKE_INSTALL_PREFIX=%s/llvm-%s" % (prefix, LLVM_VERSION),
		# 			  "-D LLVM_TARGETS_TO_BUILD=X86",
		# 			  "-D LLVM_ENABLE_TERMINFO=OFF", ".."]),
		# 	'make -j %s' % jobs,
		# 	'make install',
		# 	'make clean',
		# )),
	)

	return steps


def DepsBuild(self):
	prefix = '/opt/lib' if utils.get_linux_distribution()['short_name'] == 'centos' else '/opt'

	if self.jenkins and self.dir_blender_libs == '':
		sys.stderr.write('Running on jenkins and dir_blender_libs is missing!\n')
		sys.stderr.flush()
		sys.exit(-1)

	if self.dir_blender_libs != '':
		prefix = self.dir_blender_libs

	wd = os.path.expanduser('~/blender-libs-builds')
	if self.jenkins:
		wd = os.path.join(prefix, 'builds')

	sys.stdout.write('Blender libs build dir [%s]\n' % wd)
	sys.stdout.write('Blender libs install dir [%s]\n' % prefix)
	sys.stdout.flush()

	if not os.path.isdir(wd):
		os.makedirs(wd)

	self._blender_libs_location = prefix

	data = getDepsCompilationData(self, prefix, wd, self.build_jobs)

	if self.mode_test:
		# TODO: print out commands
		return

	sys.stdout.write('Building dependencies...\n')

	for item in data:
		sys.stdout.write('Installing %s...\n' % item[0])
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


class MacBuilder(Builder):
	def config(self):
		# Not used on OS X anymore
		pass

	def post_init(self):
		if utils.get_host_os() == utils.MAC:
			DepsBuild(self)

	def compile(self):
		cmake_build_dir = os.path.join(self.dir_build, "blender-cmake-build")
		if self.build_clean and os.path.exists(cmake_build_dir):
			utils.remove_directory(cmake_build_dir)
		if not os.path.exists(cmake_build_dir):
			os.makedirs(cmake_build_dir)

		cmake = ['cmake']

		cmake.append("-G")
		cmake.append("Ninja")

		cmake.append("-DCMAKE_BUILD_TYPE=Release")
		cmake.append('-DCMAKE_INSTALL_PREFIX=%s' % self.dir_install_path)
		cmake.append("-DWITH_VRAY_FOR_BLENDER=ON")
		cmake.append("-DWITH_MANUAL_BUILDINFO=%s" % utils.GetCmakeOnOff(self.teamcity))
		cmake.append("-DPNG_LIBRARIES=png12")

		if self.jenkins or self.teamcity_project_type == 'vb35':
			if self.teamcity_project_type == 'vb35':
				cmake.append("-DUSE_BLENDER_VRAY_ZMQ=ON")
				cmake.append("-DLIBS_ROOT=%s" % utils.path_join(self.dir_source, 'blender-for-vray-libs'))

			cmake.append("-DWITH_CXX11=ON")
			cmake.append("-DLIBDIR=%s" % utils.path_join(self.dir_source, 'lib', 'darwin-9.x.universal'))
			cmake.append("-DWITH_GAMEENGINE=OFF")
			cmake.append("-DWITH_PLAYER=OFF")
			cmake.append("-DWITH_LIBMV=OFF")
			cmake.append("-DWITH_OPENCOLLADA=OFF")
			cmake.append("-DWITH_CYCLES=ON")
			cmake.append("-DWITH_MOD_OCEANSIM=OFF")
			cmake.append("-DWITH_OPENCOLORIO=ON")
			cmake.append("-DWITH_OPENIMAGEIO=ON")
			cmake.append("-DWITH_IMAGE_OPENEXR=OFF")
			cmake.append("-DWITH_IMAGE_OPENJPEG=OFF")
			cmake.append("-DWITH_FFTW3=OFF")
			cmake.append("-DWITH_CODEC_FFMPEG=OFF")
			cmake.append("-DCMAKE_OSX_DEPLOYMENT_TARGET=")
		else:
			cmake.append("-DWITH_GAMEENGINE=%s" % utils.GetCmakeOnOff(self.with_ge))
			cmake.append("-DWITH_PLAYER=%s" % utils.GetCmakeOnOff(self.with_player))
			cmake.append("-DWITH_LIBMV=%s" % utils.GetCmakeOnOff(self.with_tracker))
			cmake.append("-DWITH_OPENCOLLADA=%s" % utils.GetCmakeOnOff(self.with_collada))
			cmake.append("-DWITH_CYCLES=%s" % utils.GetCmakeOnOff(self.with_cycles))
			cmake.append("-DWITH_MOD_OCEANSIM=ON")
			# TODO: cmake.append("-DWITH_OPENSUBDIV=ON")
			cmake.append("-DWITH_FFTW3=ON")
			cmake.append("-DWITH_ALEMBIC=ON")


		cmake.append(self.dir_blender)

		sys.stdout.write('cmake args:\n%s\n' % '\n\t'.join(cmake))
		sys.stdout.flush()

		os.chdir(cmake_build_dir)
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
		subdir = "macos" + "/" + self.build_arch

		release_path = utils.path_join(self.dir_release, subdir)

		if not self.mode_test:
			utils.path_create(release_path)

		# Example: vrayblender-2.60-42181-macos-10.6-x86_64.tar.bz2
		installer_name = utils.GetPackageName(self, ext='dmg')
		archive_name = utils.GetPackageName(self, ext='zip')
		bin_name = utils.GetPackageName(self, ext='bin')
		archive_path = utils.path_join(release_path, installer_name)

		utils.GenCGRInstaller(self, archive_path, InstallerDir=self.dir_cgr_installer)

		sys.stdout.write("Generating archive: %s\n" % archive_name)
		sys.stdout.write("  in: %s\n" % (release_path))

		cmd = "zip %s %s" % (archive_name, installer_name)

		sys.stdout.write("Calling: %s\n" % (cmd))
		sys.stdout.write("  in: %s\n" % (self.dir_install))

		if not self.mode_test:
			os.chdir(release_path)
			os.system(cmd)

		artefacts = (
			os.path.join(release_path, installer_name),
			os.path.join(release_path, bin_name),
			os.path.join(release_path, archive_name),
		)

		sys.stdout.write("##teamcity[setParameter name='env.ENV_ARTEFACT_FILES' value='%s']" % '|n'.join(artefacts))
		sys.stdout.flush()

		return subdir, archive_path.replace('.dmg', '.zip')
