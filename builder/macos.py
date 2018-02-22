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
import inspect
import platform
import subprocess
from distutils.dir_util import copy_tree

from .builder import utils
from .builder import Builder

BOOST_VERSION="1.61.0"
PYTHON_VERSION="3.6.2"
PYTHON_VERSION_BIG="3.6"
NUMPY_VERSION="1.13.1"
ZLIB_VERSION="1.2.11"

LIBS_GENERATION = 25

def getDepsCompilationData(self, prefix, wd, jobs):
	def dbg(x):
		sys.stdout.write('%s\n' % x)
		sys.stdout.flush()
		return True

	def getChDirCmd(newDir):
		return lambda: os.chdir(newDir) or True

	def getDownloadCmd(url, name):
		return lambda: dbg('wget -c %s -O %s/%s' % (url, wd, name)) and 0 == os.system('wget -c "%s" -O %s/%s' % (url, wd, name))

	def removeSoFile(path):
		if os.path.isfile(path):
			dbg('Removing so file [%s]' % path)
			os.remove(path)
			return True
		return False

	def patchPython():
		distPath = os.path.join(wd, 'Python-%s' % PYTHON_VERSION, 'Modules', 'Setup')
		with open(distPath, 'r+') as f:
			content = [l.rstrip('\n') for l in f.readlines()]
			# #zlib zlibmodule.c -I$(prefix)/include -L$(exec_prefix)/lib -lz
			sys.stdout.write('Uncommentig python config line [%s]\n' % content[364])
			sys.stdout.flush()
			content[364] = content[364][1:]
			f.seek(0)
			f.write('\n'.join(content))
			f.truncate()
		return True

	def getRemoveSoFiles(dir):
		return lambda: all([removeSoFile(path) for path in glob.glob('%s/*.dylib*')])

	steps = (
		('zlib', '%s/zlib-%s' % (prefix, ZLIB_VERSION), (
			getChDirCmd(wd),
			getDownloadCmd("https://www.zlib.net/zlib-%s.tar.gz" % ZLIB_VERSION, 'zlib.tar.gz'),
			'tar -xf zlib.tar.gz',
			getChDirCmd(os.path.join(wd, 'zlib-%s' % ZLIB_VERSION)),
			' '.join(['./configure', '--static', '--64', '--prefix=%s/zlib' % prefix]),
			'make -j %s' % jobs,
			'make install',
		)),
		('python', '%s/python-%s' % (prefix, PYTHON_VERSION), (
			getChDirCmd(wd),
			getDownloadCmd("https://www.python.org/ftp/python/%s/Python-%s.tgz" % (PYTHON_VERSION, PYTHON_VERSION), 'python.tgz'),
			'tar -xf python.tgz',
			getChDirCmd(os.path.join(wd, 'Python-%s' % PYTHON_VERSION)),
			' '.join(['./configure', '--prefix=%s/python-%s' % (prefix, PYTHON_VERSION),
					  '--libdir=%s/python-%s/lib' % (prefix, PYTHON_VERSION), '--enable-ipv6',
					  '--enable-loadable-sqlite-extensions', '--with-dbmliborder=bdb',
					  '--with-computed-gotos', '--with-pymalloc', '--with-ensurepip=install',
					  '--enable-optimizations']),
			patchPython,
			'CPPFLAGS=-I%s/zlib/include/ LDFLAGS="-L%s/zlib/lib/ -lz" make -j %s' % (prefix, prefix, jobs),
			'make install',
			'ln -s %s/python-%s %s/python' % (prefix, PYTHON_VERSION, prefix),
			'ln -s %s/python-%s %s/python-%s' % (prefix, PYTHON_VERSION, prefix, PYTHON_VERSION_BIG),
			getRemoveSoFiles('%s/python-%s/lib' % (prefix, PYTHON_VERSION))
		)),
		('numpy', '%s/numpy' % prefix, (
			getChDirCmd(wd),
			getDownloadCmd("https://github.com/numpy/numpy/releases/download/v%s/numpy-%s.tar.gz" % (NUMPY_VERSION, NUMPY_VERSION), 'numpy.tar.gz'),
			'tar -xf numpy.tar.gz',
			getChDirCmd(os.path.join(wd, 'numpy-%s' % NUMPY_VERSION)),
			'%s/python/bin/python3 setup.py install --old-and-unmanageable --prefix=%s/numpy-%s' % (prefix, prefix, NUMPY_VERSION),
			'mv %s/numpy-%s %s/numpy' % (prefix, NUMPY_VERSION, prefix) # move numpy because cmake will append numpy to the path given
		)),
	)

	return steps


def DepsBuild(self):
	prefix = self._blender_libs_location
	wd = self._blender_libs_wd

	data = getDepsCompilationData(self, prefix, wd, self.build_jobs)

	if self.mode_test:
		# TODO: print out commands
		return

	sys.stdout.write('Building dependencies...\n')

	for item in data:
		if os.path.exists(item[1]):
			sys.stdout.write('%s already installed, skipping ...\n' % item[1])
			continue

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

	return True


def PatchLibs(self):
	svn_subdirs = [
		os.path.join(self.dir_source, 'lib', 'darwin'),
		os.path.join(self.dir_source, 'lib', 'win64_vc12'),
	]

	foundLibs = 0

	for svn in svn_subdirs:
		if os.path.exists(svn) and os.path.isdir(svn):
			foundLibs += 1
			os.chdir(svn)
			utils.exec_and_log('svn --non-interactive --trust-server-cert revert . --recursive --depth=infinity', 'SVN CMD:')
			utils.exec_and_log('svn --non-interactive --trust-server-cert cleanup', 'SVN CMD:')
			utils.exec_and_log('svn --non-interactive --trust-server-cert update', 'SVN CMD:')

	if foundLibs != 2:
		utils.stdout_log('Checking out svn repos:')
		libs_prefix = self._blender_libs_location
		patch_steps = [
			"svn --non-interactive --trust-server-cert checkout --force https://svn.blender.org/svnroot/bf-blender/trunk/lib/darwin lib/darwin",
			"svn --non-interactive --trust-server-cert checkout --force https://svn.blender.org/svnroot/bf-blender/trunk/lib/win64_vc12 lib/win64_vc12",
			"cp -Rf lib/win64_vc12/opensubdiv/include/opensubdiv/* lib/darwin-9.x.universal/opensubdiv/include/opensubdiv/",
		]

		os.chdir(self.dir_source)

		for step in patch_steps:
			utils.stdout_log('MAC patch step [%s]' % step)
			os.system(step)
	else:
		utils.stdout_log('Both svn repos present!')

	pythonDest = os.path.join(self.dir_source, 'lib', 'darwin', 'python')
	pythonSource = os.path.join(libs_prefix, 'python')
	utils.stdout_log('Python patch source [%s] dest [%s]' % (pythonSource, pythonDest))
	def replace_path(path):
		destPath = os.path.join(pythonDest, path)
		sourcePath = os.path.join(pythonSource, path)
		if os.path.isdir(destPath):
			utils.stdout_log('shutil.rmtree(%s)' % destPath)
			shutil.rmtree(destPath)
			utils.stdout_log('shutil.copytree(%s, %s)' % (sourcePath, destPath))
			shutil.copytree(sourcePath, destPath)
		else:
			utils.stdout_log('os.remove(%s)' % destPath)
			os.remove(destPath)
			utils.stdout_log('shutil.copy(%s, %s)' % (sourcePath, destPath))
			shutil.copy(sourcePath, destPath)

	replace_path(os.path.join('bin', 'python3.6m'))
	replace_path(os.path.join('lib', 'libpython3.6m.a'))

	replace_path(os.path.join('lib', 'python3.6'))
	replace_path(os.path.join('include', 'python3.6m'))

	return True


class MacBuilder(Builder):
	def config(self):
		pass


	def get_cache_num(self):
		return LIBS_GENERATION


	def post_init(self):
		self.init_libs_prefix()
		if self.libs_need_clean():
			self.clean_prebuilt_libs()

		deps = DepsBuild(self)
		patch = PatchLibs(self)

		if deps and patch:
			self.libs_update_cache_number()


	def compile(self):
		cmake_build_dir = os.path.join(self.dir_build, "blender-cmake-build")
		if self.build_clean and os.path.exists(cmake_build_dir):
			utils.remove_directory(cmake_build_dir)
		if not os.path.exists(cmake_build_dir):
			os.makedirs(cmake_build_dir)

		cmake = ['cmake']

		cmake.append("-G")
		cmake.append("Ninja")

		cmake.append("-DCMAKE_BUILD_TYPE=%s" % self.build_type.capitalize())
		cmake.append('-DCMAKE_INSTALL_PREFIX=%s' % self.dir_install_path)
		cmake.append("-DWITH_VRAY_FOR_BLENDER=ON")
		cmake.append("-DWITH_MANUAL_BUILDINFO=%s" % utils.GetCmakeOnOff(self.teamcity or self.jenkins))
		cmake.append("-DPNG_LIBRARIES=png12")
		cmake.append("-DWITH_ALEMBIC=ON")
		cmake.append("-DWITH_INPUT_NDOF=ON")
		cmake.append("-DWITH_INTERNATIONAL=ON")
		cmake.append("-DWITH_PYTHON_INSTALL=ON")
		cmake.append("-DWITH_PYTHON_INSTALL_NUMPY=ON")

		cmake.append("-DWITH_GAMEENGINE=%s" % utils.GetCmakeOnOff(self.with_ge))
		cmake.append("-DWITH_PLAYER=%s" % utils.GetCmakeOnOff(self.with_player))
		cmake.append("-DWITH_LIBMV=%s" % utils.GetCmakeOnOff(self.with_tracker))
		cmake.append("-DWITH_OPENCOLLADA=%s" % utils.GetCmakeOnOff(self.with_collada))
		cmake.append("-DWITH_CYCLES=%s" % utils.GetCmakeOnOff(self.with_cycles))
		cmake.append("-DWITH_MOD_OCEANSIM=ON")
		cmake.append("-DWITH_OPENSUBDIV=OFF")
		cmake.append("-DWITH_FFTW3=ON")
		cmake.append("-DWITH_CODEC_FFMPEG=OFF")

		prefix = self._blender_libs_location
		numpyInstallPath = os.path.join(prefix, "numpy", "lib", "python%s" % PYTHON_VERSION_BIG, "site-packages")
		cmake.append("-DPYTHON_NUMPY_PATH=%s" % numpyInstallPath) # cmake will append numpy to path

		if self.with_cycles:
			cmake.append("-DWITH_LLVM=ON")
			cmake.append("-DWITH_CYCLES_OSL=ON")

		if self.build_mode == 'nightly':
			cmake.append("-DUSE_BLENDER_VRAY_ZMQ=ON")
			cmake.append("-DLIBS_ROOT=%s" % utils.path_join(self.dir_source, 'blender-for-vray-libs'))
		cmake.append("-DWITH_CXX11=ON")
		cmake.append(self.dir_blender)

		utils.stdout_log('cmake args:\n%s\n' % '\n\t'.join(cmake))
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

		installPrefix = self.dir_install_path
		blNumpyPath = os.path.join(installPrefix, 'blender.app/Contents/Resources/2.79/python/lib/python3.5/site-packages/numpy')
		plNumpyPath = os.path.join(installPrefix, 'blenderplayer.app/Contents/Resources/2.79/python/lib/python3.5/site-packages/numpy')

		for numPath in [blNumpyPath, plNumpyPath]:
			utils.remove_path(numPath)
			sourcePath = os.path.join(numpyInstallPath, 'numpy')
			utils.stdout_log('shutil.copytree(%s, %s)' % (sourcePath, numPath))
			shutil.copytree(sourcePath, numPath)


	def package(self):
		subdir = "macos" + "/" + self.build_arch

		release_path = utils.path_join(self.dir_release, subdir)
		if self.jenkins:
			utils.WritePackageInfo(self, release_path)

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
