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

from .builder import utils
from .builder import Builder

BOOST_VERSION="1.61.0"
PYTHON_VERSION="3.5.1"
PYTHON_VERSION_BIG="3.5"
NUMPY_VERSION="1.10.1"
LIBS_GENERATION = 23

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

	def getRemoveSoFiles(dir):
		return lambda: all([removeSoFile(path) for path in glob.glob('%s/*.dylib*')])

	steps = (
		# ('boost', '%s/boost-%s' % (prefix, BOOST_VERSION),(
		# 	getChDirCmd(wd),
		# 	getDownloadCmd("http://sourceforge.net/projects/boost/files/boost/%s/boost_%s.tar.bz2/download" % (BOOST_VERSION, BOOST_VERSION.replace('.', '_')), 'boost.tar.bz2'),
		# 	'tar -xf boost.tar.bz2',
		# 	'mv boost_%s boost-%s' % (BOOST_VERSION.replace('.', '_'), BOOST_VERSION),
		# 	getChDirCmd(os.path.join(wd, 'boost-%s' % BOOST_VERSION)),
		# 	'./bootstrap.sh',
		# 	'./b2 -j %s -a link=static threading=multi --layout=tagged --with-system --with-filesystem --with-thread --with-regex --with-locale --with-date_time --with-wave --prefix=%s/boost-%s --disable-icu boost.locale.icu=off install'
		# 		% (jobs, prefix, BOOST_VERSION),
		# 	'./b2 clean',
		# 	'ln -s %s/boost-%s %s/boost' % (prefix, BOOST_VERSION, prefix),
		# 	getRemoveSoFiles('%s/boost/lib' % prefix)
		# )),
		('python', '%s/python-%s' % (prefix, PYTHON_VERSION), (
			getChDirCmd(wd),
			getDownloadCmd("https://www.python.org/ftp/python/%s/Python-%s.tgz" % (PYTHON_VERSION, PYTHON_VERSION), 'python.tgz'),
			'tar -xf python.tgz',
			getChDirCmd(os.path.join(wd, 'Python-%s' % PYTHON_VERSION)),
			'./configure --prefix=%s/python-%s --libdir=%s/python-%s/lib --enable-ipv6 --enable-loadable-sqlite-extensions --with-dbmliborder=bdb --with-computed-gotos --with-pymalloc --with-ensurepip=install'
				% (prefix, PYTHON_VERSION, prefix, PYTHON_VERSION),
			'make -j %s' % jobs,
			'make install',
			'ln -s %s/python-%s %s/python' % (prefix, PYTHON_VERSION, prefix),
			'ln -s %s/python-%s %s/python-%s' % (prefix, PYTHON_VERSION, prefix, PYTHON_VERSION_BIG),
			getRemoveSoFiles('%s/python-%s/lib' % (prefix, PYTHON_VERSION))
		)),
		# ('requests', '%s/python/lib/python%s/site-packages/requests/api.py' % (prefix, PYTHON_VERSION_BIG), (
		# 	'%s/python/bin/pip%s install requests' % (prefix, PYTHON_VERSION_BIG),
		# )),
		('numpy', '%s/python/lib/python%s/site-packages/numpy' % (prefix, PYTHON_VERSION_BIG), (
			getChDirCmd(wd),
			getDownloadCmd("https://freefr.dl.sourceforge.net/project/numpy/NumPy/%s/numpy-%s.tar.gz" % (NUMPY_VERSION, NUMPY_VERSION), 'numpy.tar.gz'),
			'tar -xf numpy.tar.gz',
			getChDirCmd(os.path.join(wd, 'numpy-%s' % NUMPY_VERSION)),
			'%s/python/bin/python3 setup.py install --prefix=%s/numpy-%s' % (prefix, prefix, NUMPY_VERSION),
			'mv %s/numpy-%s %s/numpy' % (prefix, NUMPY_VERSION, prefix) # move numpy because cmake will append numpy to the path given
			#'%s/python/bin/python3 setup.py install --prefix=%s/python' % (prefix, prefix),
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
	boost_root = os.path.join(self.jenkins_kdrive_path, 'boost', 'boost_1_61_0')

	mac_version_names = {
		"10.9": "mavericks",
		"10.8": "mountain_lion",
		"10.6": "snow_leopard",
	}

	mac_version = '.'.join(platform.mac_ver()[0].split('.')[0:2])
	mac_name = mac_version_names[mac_version] if mac_version in mac_version_names else None
	sys.stdout.write('Mac ver full [%s] -> %s == %s\n' % (str(platform.mac_ver()), mac_version, mac_name))
	sys.stdout.flush()

	boost_lib = os.path.join(boost_root, 'lib', '%s_x64' % mac_name)

	if not mac_name or not os.path.exists(boost_lib):
		sys.stderr.write('Boost path [%s] missing for this version of mac!\n' % boost_lib)
		sys.stderr.flush()

		mac_name = mac_version_names['10.9']
		boost_lib = os.path.join(boost_root, 'lib', '%s_x64' % mac_name)

		if not mac_name or not os.path.exists(boost_lib):
			sys.stderr.write('Boost path [%s] missing for this version of mac... exiting!\n' % boost_lib)
			sys.stderr.flush()
			sys.exit(1)
		else:
			sys.stderr.write('Trying to build with [%s] instead!\n' % boost_lib)
			sys.stderr.flush()

	boost_lib_dir = os.path.join(boost_lib, 'gcc-4.2-cpp')

	svn_subdirs = [
		os.path.join(self.dir_source, 'lib', 'darwin-9.x.universal'),
		os.path.join(self.dir_source, 'lib', 'darwin'),
		os.path.join(self.dir_source, 'lib', 'win64_vc12'),
	]

	for svn in svn_subdirs:
		if os.path.exists(svn) and os.path.isdir(svn):
			sys.stdout.write('reverting all changes in [%s] \n' % svn)
			sys.stdout.flush()
			os.chdir(svn)
			os.system('svn revert -R .')

	python_patch = os.path.join(self.dir_source, 'blender-for-vray-libs', 'Darwin', 'pyport.h')
	libs_prefix = self._blender_libs_location
	patch_steps = [
		"svn --non-interactive --trust-server-cert checkout --force https://svn.blender.org/svnroot/bf-blender/trunk/lib/darwin-9.x.universal lib/darwin-9.x.universal",
		"svn --non-interactive --trust-server-cert checkout --force https://svn.blender.org/svnroot/bf-blender/trunk/lib/darwin lib/darwin",
		"svn --non-interactive --trust-server-cert checkout --force https://svn.blender.org/svnroot/bf-blender/trunk/lib/win64_vc12 lib/win64_vc12",
		"cp -Rf lib/win64_vc12/opensubdiv/include/opensubdiv/* lib/darwin-9.x.universal/opensubdiv/include/opensubdiv/",
		# "mv lib/darwin/python lib/darwin/python-orig",
		# "cp -Rf lib/darwin-9.x.universal/python lib/darwin/python",
		#"rm -rf lib/darwin/python",
		#"cp -Rf %s/python-%s lib/darwin/python" % (libs_prefix, PYTHON_VERSION),
		#"cp lib/darwin/python/lib/libpython3.5m.a lib/darwin/python/lib/python3.5/",
		# "cp lib/darwin-9.x.universal/png/lib/libpng12.a lib/darwin-9.x.universal/png/lib/libpng.a",
		# "cp lib/darwin-9.x.universal/png/lib/libpng12.la lib/darwin-9.x.universal/png/lib/libpng.la",
		# "cp -f %s lib/darwin-9.x.universal/python/include/python3.5m/pyport.h" % python_patch,
		#"cp -f %s lib/darwin/python/include/python3.5m/pyport.h" % python_patch,
	]

	os.chdir(self.dir_source)

	for step in patch_steps:
		sys.stdout.write('MAC patch step [%s]\n' % step)
		sys.stdout.flush()
		os.system(step)

	# sys.stdout.write('PY LIBS: [%s]' % '\n'.join(glob.glob('lib/darwin/python/lib/*')))
	# sys.stdout.write('PY LIBS: [%s]' % '\n'.join(glob.glob('lib/darwin/python/lib/python3.5/*')))
	# sys.stdout.flush()

	return True



class MacBuilder(Builder):
	def config(self):
		# Not used on OS X anymore
		pass


	def get_cache_num(self):
		return LIBS_GENERATION


	def post_init(self):
		self.init_libs_prefix()
		if self.libs_need_clean():
			self.clean_prebuilt_libs()

		deps = DepsBuild(self)
		patch = PatchLibs(self)

		prefix = self._blender_libs_location
		source = os.path.join(prefix, 'numpy')
		dest = os.path.join(prefix, 'python')
		utils.stdout_log('shutil.copytree(%s, %s)' % (source, dest))
		shutil.copytree(source, dest)

		for f in utils.dir_contents_recursive(dest):
			utils.stdout_log('DEST FILE: [%s]' % f)

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
		cmake.append("-DPYTHON_NUMPY_PATH=%s" % prefix) # cmake will append numpy to path

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
