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
import subprocess

from .builder import utils
from .builder import Builder


class WindowsBuilder(Builder):
	def setup_msvc_2013(self, cgrepo):
		env = {
			'INCLUDE' : [
				"{CGR_SDK}/msvs2013/PlatformSDK/Include/shared",
				"{CGR_SDK}/msvs2013/PlatformSDK/Include/um",
				"{CGR_SDK}/msvs2013/PlatformSDK/Include/winrt",
				"{CGR_SDK}/msvs2013/PlatformSDK/Include/ucrt",
				"{CGR_SDK}/msvs2013/include",
				"{CGR_SDK}/msvs2013/atlmfc/include",
			],

			'LIB' : [
				"{CGR_SDK}/msvs2013/PlatformSDK/Lib/winv6.3/um/x64",
				"{CGR_SDK}/msvs2013/PlatformSDK/Lib/ucrt/x64",
				"{CGR_SDK}/msvs2013/atlmfc/lib/amd64",
				"{CGR_SDK}/msvs2013/lib/amd64",
			],

			'PATH' : [
					"{CGR_SDK}/msvs2013/bin/amd64",
					"{CGR_SDK}/msvs2013/bin",
					"{CGR_SDK}/msvs2013/PlatformSDK/bin/x64",
				] + os.environ['PATH'].split(';')
			,
		}
		os.environ['__MS_VC_INSTALL_PATH'] = "{CGR_SDK}/msvs2013"
		for var in env:
			os.environ[var] = ";".join(env[var]).format(CGR_SDK=cgrepo)


	def compile(self):
		cmake_build_dir = os.path.join(self.dir_build, "blender-cmake-build")
		if self.build_clean and os.path.exists(cmake_build_dir):
			utils.remove_directory(cmake_build_dir)
		if not os.path.exists(cmake_build_dir):
			os.makedirs(cmake_build_dir)
		os.chdir(cmake_build_dir)

		if self.mode_test:
			return

		cmake = ['cmake']

		cmake.append("-G")
		cmake.append("Ninja")

		old_path = ''
		if self.jenkins:
			cmake[0] = utils._get_cmd_output('where cmake')
			old_path = os.environ['PATH']
			os.environ['PATH'] = utils.path_join(self.patch_dir, "tools")
			self.setup_msvc_2013(os.environ['JENKINS_WIN_SDK_PATH'])

		cmake.append("-DCMAKE_BUILD_TYPE=Release")
		cmake.append('-DCMAKE_INSTALL_PREFIX=%s' % self.dir_install_path)

		cmake.append("-DWITH_VRAY_FOR_BLENDER=ON")
		cmake.append("-DWITH_MANUAL_BUILDINFO=%s" % utils.GetCmakeOnOff(self.teamcity))

		if self.teamcity_project_type == 'vb35':
			cmake.append("-DUSE_BLENDER_VRAY_ZMQ=ON")
			cmake.append("-DLIBS_ROOT=%s" % utils.path_join(self.dir_source, 'blender-for-vray-libs'))

		cmake.append("-DWITH_GAMEENGINE=%s" % utils.GetCmakeOnOff(self.with_ge))
		cmake.append("-DWITH_PLAYER=%s" % utils.GetCmakeOnOff(self.with_player))
		cmake.append("-DWITH_LIBMV=%s" % utils.GetCmakeOnOff(self.with_tracker))
		cmake.append("-DWITH_OPENCOLLADA=%s" % utils.GetCmakeOnOff(self.with_collada))
		cmake.append("-DWITH_MOD_OCEANSIM=ON")
		cmake.append("-DWITH_OPENSUBDIV=ON")
		cmake.append("-DWITH_FFTW3=ON")

		cmake.append(self.dir_blender)

		sys.stdout.write('PATH:\n\t%s\n' % '\n\t'.join(os.environ['PATH'].split(';')))
		sys.stdout.write('cmake args:\n%s\n' % '\n\t'.join(cmake))
		sys.stdout.flush()

		res = subprocess.call(cmake)
		if not res == 0:
			sys.stderr.write("There was an error during configuration!\n")
			sys.exit(1)

		self.write_buildinfo(cmake_build_dir)

		ninja = utils.path_join(self.patch_dir, "tools", "ninja.exe")

		make = [ninja]
		make.append('-j%s' % self.build_jobs)
		make.append('install')

		res = subprocess.call(make)
		if not res == 0:
			sys.stderr.write("There was an error during the compilation!\n")
			sys.exit(1)

		if self.jenkins:
			os.environ['PATH'] = old_path


	def config(self):
		# Not used on Windows anymore
		pass


	def installer_cgr(self, installer_path):
		utils.GenCGRInstaller(self, installer_path, InstallerDir=self.dir_cgr_installer)


	def package(self):
		subdir = "windows" + "/" + self.build_arch

		release_path = os.path.join(self.dir_release, subdir)

		if not self.mode_test:
			utils.path_create(release_path)

		# Example: vrayblender-2.60-42181-windows-x86_64.exe
		installer_name = utils.GetPackageName(self)
		zip_name = utils.GetPackageName(self, ext='zip')
		installer_path = utils.path_slashify(utils.path_join(release_path, installer_name))
		installer_root = utils.path_join(self.dir_source, "vb25-patch", "installer")

		if self.use_installer == 'CGR':
			self.installer_cgr(installer_path)

			cmd = "7z -tzip a %s %s" % (zip_name, installer_name)

			sys.stdout.write("Calling: %s\n" % (cmd))
			sys.stdout.write("  in: %s\n" % (release_path))

			if not self.mode_test:
				os.chdir(release_path)
				os.system(cmd)

			artefacts = (
				os.path.normpath(os.path.join(release_path, installer_name)),
				os.path.normpath(os.path.join(release_path, zip_name)),
			)

			sys.stdout.write("##teamcity[setParameter name='env.ENV_ARTEFACT_FILES' value='%s']" % '|n'.join(artefacts))
			sys.stdout.flush()

			return subdir, zip_name

		# Use NSIS log plugin
		installer_log  = False

		sys.stdout.write("Generating NSIS installer: %s\n" % (installer_name))
		sys.stdout.write("  in: %s\n" % (installer_path))

		nsis = open(utils.path_join(installer_root, "template.nsi"), 'r').read()

		nsis = nsis.replace('{IF64}', '64' if self.build_arch == 'x86_64' else "")
		nsis = nsis.replace('{INSTALLER_SCRIPT_ROOT}', installer_root)
		nsis = nsis.replace('{INSTALLER_OUTFILE}', installer_path)
		nsis = nsis.replace('{VERSION}', self.version)
		nsis = nsis.replace('{REVISION}', self.revision)

		director_size = 0

		installer_files   = ""
		uninstaller_files = []

		for dirpath, dirnames, filenames in os.walk(self.dir_install_path):
			if dirpath.startswith('.svn'):
				continue
			if dirpath.endswith('__pycache__'):
				continue

			_dirpath = os.path.normpath(dirpath).replace( os.path.normpath(self.dir_install_path), "" )

			if installer_log:
				installer_files += '\tStrCpy $VB_TMP "$INSTDIR%s"\n' % (_dirpath)
				installer_files += '\t${SetOutPath} $VB_TMP\n'
			else:
				installer_files += '\tSetOutPath "$INSTDIR%s"\n' % (_dirpath)
				uninstaller_files.append( '\tRMDir "$INSTDIR%s"\n' % (os.path.normpath(_dirpath)) )

			for f in os.listdir(dirpath):
				f_path = os.path.join(dirpath, f)

				if os.path.isdir(f_path):
					continue

				basepath, basename = os.path.split(f_path)

				if installer_log:
					installer_files += '\t${File} "%s" "%s" "$VB_TMP"\n' % (basepath, basename)
				else:
					installer_files += '\tFile "%s"\n' % (f_path)
					uninstaller_files.append( '\tDelete "$INSTDIR%s\%s"\n' % (_dirpath, basename) )

				director_size += os.path.getsize(f_path)

		uninstaller_files.reverse()

		installer_dir = utils.path_join(self.dir_source, "vb25-patch", "installer")

		if installer_log:
			uninstall_stuff = open(utils.path_join(installer_dir, 'uninstall_log.tmpl'), 'r').read()
		else:
			uninstall_stuff = ''.join(uninstaller_files)

		nsis = nsis.replace('{INSTALLER_FILES}', installer_files)
		nsis = nsis.replace('{UNINSTALLER_FILES}', uninstall_stuff)
		nsis = nsis.replace('{SIZE}', str(director_size / 1024))

		template = utils.path_join(installer_dir, "installer.nsi")

		open(template, 'w').write(nsis)

		makensis_exe = utils.find_makensis()

		cmd= []
		cmd.append(makensis_exe)
		cmd.append(template)

		sys.stdout.write("Calling: %s\n" % (' '.join(cmd)))

		if not self.mode_test:
			os.chdir(installer_dir)
			proc = subprocess.call(cmd)

		return subdir, installer_path

	def package_archive(self):
		subdir = "windows" + "/" + self.build_arch

		release_path = os.path.join(self.dir_release, subdir)

		if not self.mode_test:
			utils.path_create(release_path)

		archive_name = utils.GetPackageName(self, ext="zip")
		archive_path = utils.path_join(release_path, archive_name)

		sys.stdout.write("Generating archive: %s\n" % (archive_name))
		sys.stdout.write("  in: %s\n" % (release_path))

		cmd = "7z -tzip a %s %s" % (archive_path, self.dir_install_name)

		sys.stdout.write("Calling: %s\n" % (cmd))
		sys.stdout.write("  in: %s\n" % (self.dir_install))

		if not self.mode_test:
			os.chdir(self.dir_install)
			os.system(cmd)

		return subdir, archive_path


	def post_init(self):
		pass
