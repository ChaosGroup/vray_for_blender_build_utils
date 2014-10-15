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

from builder import utils
from builder import Builder


class WindowsBuilder(Builder):
	def config(self):
		sys.stdout.write("Generating build configuration:\n")
		sys.stdout.write("  in: %s\n" % (self.user_config))

		if self.mode_test:
			return

		if self.user_user_config:
			open(self.user_config, 'w').write(open(self.user_user_config, 'r').read())
			return

		uc= open(self.user_config, 'w')

		build_options= {
			'True': [
				'WITH_BF_FFMPEG',
				'WITH_BF_OPENAL',
				'WITH_BF_SDL',
				'WITH_BF_BULLET',
				'WITH_BF_ZLIB',
				'WITH_BF_FTGL',
				'WITH_BF_RAYOPTIMIZATION',
				'WITH_BUILDINFO',
				'WITH_BF_OPENEXR',
				'WITH_BF_ICONV',
			],
			'False': [
				'WITH_BF_FREESTYLE',
				'WITH_BF_QUICKTIME',
				'WITH_BF_FMOD',
				'WITH_BF_VERSE',
				'WITH_BF_JACK',
				'WITH_BF_FFTW3',
			]
		}

		if self.with_ge:
			build_options['True'].append('WITH_BF_GAMEENGINE')
		else:
			build_options['False'].append('WITH_BF_GAMEENGINE')

		if self.with_player:
			build_options['True'].append('WITH_BF_PLAYER')
		else:
			build_options['False'].append('WITH_BF_PLAYER')

		if not self.with_tracker:
			build_options['False'].append('WITH_BF_LIBMV')

		if self.build_arch == 'x86_64':
			build_options['False'].append('WITH_BF_JACK')
			build_options['False'].append('WITH_BF_SNDFILE')
			build_options['False'].append('WITH_BF_FFMPEG')
			build_options['False'].append('WITH_BF_OPENAL')

			uc.write("BF_PNG_LIB = 'libpng'\n")
			uc.write("\n")

		if self.use_collada:
			build_options['True'].append('WITH_BF_COLLADA')
		else:
			build_options['False'].append('WITH_BF_COLLADA')

		if self.use_debug:
			build_options['True'].append('BF_DEBUG')

		# Windows git/scons issue - scons can't clear installation directory
		# when vb25 .git is installed
		if os.path.exists(self.dir_install_path):
			os.system("rmdir /Q /S %s" % (self.dir_install_path))

		uc.write("BF_INSTALLDIR     = '%s'\n" % (self.dir_install_path))
		uc.write("BF_BUILDDIR       = '%s'\n" % (self.dir_build))
		uc.write("BF_SPLIT_SRC      = True\n")
		uc.write("BF_TWEAK_MODE     = False\n")
		uc.write("BF_NUMJOBS        = %s\n" % (self.build_threads))

		# Cycles
		#
		if not self.with_cycles:
			uc.write("WITH_BF_CYCLES    = False\n")
			uc.write("WITH_BF_OIIO      = False\n")
			uc.write("\n")

		uc.write("WITH_VRAY_FOR_BLENDER = True\n")

		# Write boolean options
		for key in build_options:
			for opt in build_options[key]:
				uc.write("{0:25} = {1}\n".format(opt, key))

		uc.write("\n")
		uc.close()


	def installer_cgr(self, installer_path):
		def unix_slashes(path):
			p = os.path.normpath(path.replace("\\", "/"))
			return p

		InstallerDir = "H:/devel/vrayblender/cgr_installer"

		sys.stdout.write("Generating CGR installer:\n")
		sys.stdout.write("  %s\n" % installer_path)

		# Collect installer files
		#
		removeJunk   = set()
		installerFiles = []

		for dirpath, dirnames, filenames in os.walk(self.dir_install_path):
			if dirpath.startswith('.svn') or dirpath.endswith('__pycache__'):
				continue

			rel_dirpath = os.path.normpath(dirpath).replace(os.path.normpath(self.dir_install_path), "")

			for f in os.listdir(dirpath):
				f_path = os.path.join(dirpath, f)
				if os.path.isdir(f_path):
					continue

				relInstDir  = unix_slashes(rel_dirpath)
				absFilePath = unix_slashes(f_path)

				removeJunk.add('\t\t\t<Files Dest="[INSTALL_ROOT]%s" DeleteDirs="1">*.pyc</Files>' % (relInstDir))
				removeJunk.add('\t\t\t<Files Dest="[INSTALL_ROOT]%s" DeleteDirs="1">__pycache__</Files>' % (relInstDir))
				installerFiles.append('\t\t\t<FN Dest="[INSTALL_ROOT]%s">%s</FN>' % (relInstDir, absFilePath))

		# Write installer template
		#
		tmpl = open("%s/cgr_template.xml" % InstallerDir, 'r').read()
		tmplFinal = "%s/installer.xml" % InstallerDir

		with open(tmplFinal, 'w') as f:
			tmpl = tmpl.replace("${APP_TITLE}",      "Blender (With V-Ray Additions)")
			tmpl = tmpl.replace("${APP_TITLE_FULL}", "Blender ${VERSION_MAJOR}.${VERSION_MINOR} (With V-Ray Additions)")

			# Files
			tmpl = tmpl.replace("${FILE_LIST}", "\n".join(sorted(reversed(installerFiles))))
			tmpl = tmpl.replace("${RUNTIME_JUNK_LIST}", "\n".join(sorted(removeJunk)))

			# Versions
			tmpl = tmpl.replace("${VERSION_MAJOR}", self.versionArr[1])
			tmpl = tmpl.replace("${VERSION_MINOR}", self.versionArr[2])
			tmpl = tmpl.replace("${VERSION_SUB}",   self.versionArr[3])
			tmpl = tmpl.replace("${VERSION_CHAR}",  self.versionArr[4])

			tmpl = tmpl.replace("${VERSION_HASH}",       self.brev)
			tmpl = tmpl.replace("${VERSION_PATCH_HASH}", self.revision)

			# Installer stuff
			tmpl = tmpl.replace("${INSTALLER_DATA_ROOT}", InstallerDir)

			# System stuff
			tmpl = tmpl.replace("${PLATFORM}", "x86_64")

			f.write(tmpl)

		# Run installer generator
		#
		packer = ["%s/bin/packer.exe" % InstallerDir]
		# packer.append('-debug=1')
		packer.append('-exe')
		packer.append('-xml=%s' % unix_slashes(tmplFinal))
		packer.append('-filesdir=%s' % unix_slashes(InstallerDir))
		packer.append('-dest=%s' % installer_path)
		packer.append('-installer=%s' % "%s/bin/installer.exe" % InstallerDir)
		packer.append('-outbin=%s' % "C:/tmp/out.bin")
		packer.append('-wmstr=""')
		packer.append('-wmval=""')

		subprocess.call(packer)


	def package(self):
		subdir = "windows" + "/" + self.build_arch

		release_path = os.path.join(self.dir_release, subdir)

		if not self.mode_test:
			utils.path_create(release_path)

		# Example: vrayblender-2.60-42181-windows-x86_64.exe
		installer_name = utils.GetPackageName(self)
		installer_path = utils.path_slashify(utils.path_join(release_path, installer_name))
		installer_root = utils.path_join(self.dir_source, "vb25-patch", "installer")

		if self.with_installer == 'CGR':
			self.installer_cgr(installer_path)
			return

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


	def post_init(self):
		pass
