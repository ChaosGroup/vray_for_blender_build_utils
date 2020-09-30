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
import re
import sys
import shutil
import tempfile
import subprocess
import datetime

from . import utils

PREBUILD_LIB_NUMBER = 13

OFFICIAL_REPO = "http://git.blender.org/blender.git"
GITHUB_REPO   = "https://github.com/ChaosGroup/blender_with_vray_additions"

BLENDER_HASH_271 = "772af36fc469e7666fc59d1d0b0e4dbcf52cfe2c"


class Builder:
	"""
	  A generic build class.
	"""

	def __init__(self, params):
		# Store options as attrs
		for p in params:
			setattr(self, p, params[p])

		self.project        = "vrayblender" + self.target_version_suffix
		self.version        = utils.VERSION
		self.revision       = utils.REVISION
		self.brev           = ""
		self.commits        = '0'

		# Installation diractory name
		self.dir_install_name = "vrayblender"
		self.dir_install_path = utils.path_join(self.dir_install, self.dir_install_name)

		# Host info
		self.host_os        = utils.get_host_os()
		self.host_arch      = utils.get_host_architecture()
		self.host_name      = utils.get_hostname()
		self.host_username  = utils.get_username()
		self.host_linux     = utils.get_linux_distribution()

		self.patch_dir = utils.path_join(os.path.dirname(os.path.realpath(__file__)), '..')

		# Build architecture
		self.build_arch     = self.host_arch


	def get_cache_num(self):
		raise ValueError()


	def info(self):
		sys.stdout.write("\n")
		sys.stdout.write("Build information:\n")

		sys.stdout.write("OS: %s\n" % (self.host_os.title()))

		if self.host_os == utils.LNX:
			sys.stdout.write("Distribution: %s %s\n" % (self.host_linux["long_name"], self.host_linux["version"]))

		sys.stdout.write("Architecture: %s\n" % (self.host_arch))
		sys.stdout.write("Build architecture: %s\n" % (self.build_arch))
		sys.stdout.write("Target: %s %s (%s)\n" % (self.project, self.version, self.revision))
		sys.stdout.write("Source directory:  %s\n" % (self.dir_source))
		sys.stdout.write("Build directory:   %s\n" % (self.dir_build))
		sys.stdout.write("Install directory: %s\n" % (self.dir_install_path))
		sys.stdout.write("Release directory: %s\n" % (self.dir_release))
		sys.stdout.write("\n")


	def xpak_pak_install(self, pakAndVersion):
		binToolsRoot = os.path.join(self.dir_source, 'bintools')
		osDir = {
			utils.WIN: 'x64',
			utils.LNX: 'linux_x64',
			utils.MAC: 'mavericks_x64',
		}[utils.get_host_os()]

		executableName = 'xpaktool'
		if utils.get_host_os() == utils.WIN:
			executableName = executableName + '.exe'

		xpakTool = os.path.join(binToolsRoot, 'bintools', osDir, executableName)
		xpakInstall = "%s xinstall -pak %s -workdir %s" % (xpakTool, pakAndVersion, self.xpak_path)
		return utils.exec_and_log(xpakInstall, 'XPAK', exit=True)

	def get_svn_libs(self):
		if utils.get_host_os() == utils.LNX:
			sys.stdout.write('Skipping svn libs for linux.\n')
			sys.stdout.flush()
			return

		if self.jenkins and utils.get_host_os() == utils.MAC:
			sys.stdout.write('Skipping svn libs for jenkins mac.\n')
			sys.stdout.flush()
			return

		svn_exec = lambda cmd: utils.exec_and_log(cmd, 'SVN', exit=True)

		# Update Blender libs
		if self.upblender == 'on' or self.jenkins:
			revisionSuffix = ''
			if self.svn_revision != '':
				revisionSuffix = '@%s' % str(self.svn_revision)
			lib_dir = None
			svn_cmd = None
			if self.host_os != utils.LNX:
				if self.host_os == utils.WIN:
					lib_dir = utils.path_join(self.dir_source, "lib", "win64_vc15")
					svn_cmd = "svn checkout https://svn.blender.org/svnroot/bf-blender/trunk/lib/win64_vc15%s lib/win64_vc15" % revisionSuffix
				elif self.host_os == utils.MAC:
					lib_dir = utils.path_join(self.dir_source, "lib", "darwin-9.x.universal")
					svn_cmd = "svn checkout https://svn.blender.org/svnroot/bf-blender/trunk/lib/darwin%s lib/darwin-9.x.universal" % revisionSuffix

				sys.stdout.write('Lib dir: [%s]\n' % lib_dir)
				sys.stdout.flush()
				if not os.path.exists(lib_dir):
					sys.stdout.write("Getting \"lib\" data... [%s]\n" % svn_cmd)
					sys.stdout.flush()
					if not self.mode_test:
						os.chdir(self.dir_source)
						svn_exec(svn_cmd)
				else:
					sys.stdout.write("Updating \"lib\" data... [svn update]\n")
					sys.stdout.flush()
					if not self.mode_test:
						os.chdir(lib_dir)
						utils.remove_directory(os.path.join(lib_dir, 'release', 'site-packages'))
						svn_exec("svn cleanup")
						svn_exec("svn revert . --recursive --depth=infinity")
						svn_exec("svn cleanup")
					if self.svn_revision == '':
						svn_exec("svn update")

				if self.svn_revision != '':
					os.chdir(lib_dir)
					svn_exec("svn up -r%s" % self.svn_revision)

	def update_sources(self):
		"""
		  Getting/updating sources
		"""

		def exportSources():
			sys.stdout.write("Exporting sources...\n")
			if self.mode_test:
				return

			if os.path.exists(self.dir_blender):
				utils.remove_directory(self.dir_blender)

			# Copy full tree to have proper build info.
			shutil.copytree(self.dir_blender_svn, self.dir_blender)

			# Update patched branch
			os.chdir(self.dir_blender)
			os.system("git remote update github")
			os.system("git checkout -b {branch} github/{branch}".format(branch=self.use_github_branch))

		# Update Blender sources
		if self.upblender == "on":
			if os.path.exists(self.dir_blender):
				sys.stdout.write("Removing exported sources...\n")
				if not self.mode_test:
					utils.remove_directory(self.dir_blender)

			if not os.path.exists(self.dir_blender_svn):
				sys.stdout.write("Obtaining Blender sources...\n")
				if not self.mode_test:
					os.chdir(self.dir_source)

					# Obtain sources
					os.system("git clone %s blender-git" % GITHUB_REPO)
					os.chdir(self.dir_blender_svn)

					# Change remotes for correct submodule init
					os.system("git remote set-url origin %s" % OFFICIAL_REPO)
					os.system("git remote add github %s" % GITHUB_REPO)

					# Init submodules
					os.system("git submodule update --init --recursive")
					os.system("git submodule foreach git checkout master")
					os.system("git submodule foreach git pull --rebase origin master")

			else:
				sys.stdout.write("Updating Blender sources...\n")
				if not self.mode_test:
					os.chdir(self.dir_blender_svn)

					# Update submodules
					os.system("git submodule foreach git pull --rebase origin master")

			exportSources()

		self.get_svn_libs()
		# Update V-Ray/Blender patchset
		if self.uppatch == "on" and not self.mode_developer:

			if os.path.exists(self.patch_dir):
				sys.stdout.write("Updating V-Ray/Blender patches...\n")
				if not self.mode_test:
					os.chdir(self.patch_dir)
					os.system("git pull")
			else:
				sys.stdout.write("Getting V-Ray/Blender patches...\n")
				if not self.mode_test:
					os.chdir(self.dir_source)
					os.system("git clone git://github.com/ChaosGroup/vray_for_blender_build_utils vb25-patch")


	def update(self):
		self.revision, self.brev, self.commits = utils.get_svn_revision(self.dir_blender)

		self.version = utils.get_blender_version(self.dir_blender)[0]
		self.versionArr = utils.get_blender_version(self.dir_blender)

		self.dir_install_name = utils.GetInstallDirName(self)
		self.dir_install_path = utils.path_join(self.dir_install, self.dir_install_name)


	def patch(self):
		patch_dir = self.patch_dir

		if self.use_blender_hash:
			patchBin      = utils.find_patch()
			patchFilepath = os.path.join(tempfile.gettempdir(), "vray_for_blender.patch")

			os.chdir(self.dir_blender)

			os.system("git checkout %s" % self.use_github_branch) # Checkout exporter branch
			os.system("git diff master > %s" % patchFilepath)     # Generate diff with master
			os.system("git fetch --tags")                         # Hash could be tag also
			os.system("git checkout %s" % self.use_blender_hash)  # Checkout needed revision
			os.system("git checkout -b vray_for_blender")         # Create some branch for patching
			os.system("patch -Np1 -i %s" % patchFilepath)         # Apply patch

			os.remove(patchFilepath)

		# Add datafiles: splash, default scene etc
		sys.stdout.write("Adding datafiles...\n")

		datafiles_path = utils.path_join(self.dir_blender, "release", "datafiles")

		if not self.mode_test:
			# Change splash
			for splash_filename in ["splash.png", "splash_2x.png"]:
				splash_path_src = utils.path_join(patch_dir, "datafiles", splash_filename)
				splash_path_dst = utils.path_join(datafiles_path, splash_filename)

				shutil.copyfile(splash_path_src, splash_path_dst)

			# Change icons
			for subdir in ["blender_icons16", "blender_icons32"]:
				icons_path_src = utils.path_join(patch_dir, "datafiles", subdir)
				icons_path_dst = utils.path_join(datafiles_path, subdir)

				for fileName in os.listdir(icons_path_src):
					iconFilepathSrc = os.path.join(icons_path_src, fileName)
					iconFilepathDst = os.path.join(icons_path_dst, fileName)

					shutil.copyfile(iconFilepathSrc, iconFilepathDst)


	def clean_prebuilt_libs(self):
		""" Delete all files and dirs inside self._blender_libs_location dir 
		"""
		prefix = self._blender_libs_location
		wd = self._blender_libs_wd
		utils.stdout_log("Clearing prebuilt libs location [%s]")

		utils.delete_dir_contents(prefix)

		if not os.path.isdir(wd):
			os.makedirs(wd)


	def get_libs_cache_file_path(self):
		""" Get the full path to the prebuilt_cache.txt file
		"""
		return os.path.join(self._blender_libs_location, "prebuilt_cache.txt")


	def libs_need_clean(self):
		""" Check prebuilt_cache.txt to see if it exists and if it does
		check if the version inside is equal to ours (self.get_cache_num())
		"""
		prefix = self._blender_libs_location
		cache_file = self.get_libs_cache_file_path()
		utils.stdout_log("Trying to open cache file [%s]" % cache_file)

		if not os.path.exists(cache_file):
			utils.stdout_log("Cache file does not exist [%s]" % cache_file)
			return True

		with open(cache_file, "r") as file:
			contents = file.read()
			file_data = int(contents)
			utils.stdout_log("Cache file contents [%s] = parsed version %d <=> script version %d" % (contents, file_data, self.get_cache_num()))
			if file_data < self.get_cache_num():
				utils.stdout_log("Cache is older than our version")
				return True

		utils.stdout_log("Cache is updated enough, will not clear")
		return False


	def libs_update_cache_number(self):
		""" Update prebuilt_cache.txt with self.get_cache_num()
		"""
		cache_file = self.get_libs_cache_file_path()
		utils.stdout_log("Trying to open cache file [%s]" % cache_file)

		with open(cache_file, "w") as file:
			utils.stdout_log("Updating cache file to %s" % str(self.get_cache_num()))
			file.write(str(self.get_cache_num()))


	def init_libs_prefix(self):
		""" Determine what path will be used for prebuilt libs
		and what path will be used as temp dir for building the libs
		"""
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

		utils.stdout_log('Blender libs build dir [%s]' % wd)
		utils.stdout_log('Blender libs install dir [%s]' % prefix)

		if not os.path.isdir(wd):
			os.makedirs(wd)

		self._blender_libs_wd = wd
		self._blender_libs_location = prefix
		return prefix


	def post_init(self):
		"""
		  Override this method in subclass.
		"""
		pass


	def init_paths(self):
		if self.package:
			if not self.mode_test:
				utils.path_create(self.dir_release)

		self.dir_build        = utils.path_slashify(self.dir_build)
		self.dir_source       = utils.path_slashify(self.dir_source)
		self.dir_install_path = utils.path_slashify(self.dir_install_path)

		self.dir_blender      = utils.path_join(self.dir_source, "blender")
		self.dir_blender_svn  = utils.path_join(self.dir_source, "blender-git")
		self.xpak_path = os.path.join(self.dir_source, 'xpak-workdir')
		utils.path_create(self.xpak_path)


	def compile(self):
		"""
		  Override this method in subclass.
		"""
		sys.stderr.write("Base class method called: package() This souldn't happen.\n")


	def compile_post(self):
		pass


	def exporter(self):
		"""
		  Add script and modules
		"""
		scriptsPath = utils.path_join(self.dir_install, self.dir_install_name, self.version, "scripts")
		if self.host_os == utils.MAC:
			scriptsPath = utils.path_join(self.dir_install, self.dir_install_name, "blender.app", "Contents", "Resources", self.version, "scripts")

		addonsPath  = utils.path_join(scriptsPath, "addons")

		sys.stdout.write("Adding exporter to:\n    %s\n" % addonsPath)

		if not self.mode_test:
			if not os.path.exists(addonsPath):
				sys.stderr.write("Something went wrong! Can't add Python modules and exporter!\n")
				sys.exit(3)

			os.chdir(addonsPath)
			exporterPath = utils.path_join(addonsPath, "vb30")
			if os.path.exists(exporterPath):
				utils.remove_directory(exporterPath)
			utils.stdout_log("Cloning vb30 to [%s]" % addonsPath)
			os.system("git clone --recursive git@git.chaosgroup.com:blender/vray_for_blender_python_exporter.git vb30")

			if self.use_exp_branch not in {'master'}:
				os.chdir(exporterPath)
				os.system("git remote update")
				os.system("git checkout -b {branch} origin/{branch}".format(branch=self.use_exp_branch))

			os.chdir(exporterPath)
			os.system("git submodule update --init --recursive")

	def package(self):
		"""
		  Override this method in subclass.
		"""
		sys.stderr.write("Base class method called: package() This souldn't happen.\n")

	def build_zmq(self):
		saveDir = os.getcwd()
		buildPath = os.path.join(self.dir_build, 'vrayserverzmq-cmake-build')
		if not os.path.exists(buildPath):
			os.makedirs(buildPath)
		os.chdir(buildPath)

		command = [sys.executable]
		command.append(os.path.join(self.dir_source, 'vrayserverzmq', 'build', 'builder.py'))
		command.append('--source_path=%s' % os.path.join(self.dir_source, 'vrayserverzmq'))
		command.append('--libs_path=%s' % utils.path_join(self.dir_source, 'blender-for-vray-libs'))
		command.append('--xpak_path=%s' % self.xpak_path)
		command.append('--install_path=%s' % os.path.normpath(os.path.join(self.dir_install, '..', 'vrayserverzmq')))

		sys.stdout.write('Calling builder:\n%s\n' % '\n\t'.join(command))
		sys.stdout.flush()

		res = subprocess.call(command, cwd=buildPath)
		if res != 0:
			sys.stderr.write('Failed compilation of vrayserverzmq\n')
			sys.stderr.flush()
			sys.exit(-1)

		os.chdir(saveDir)

	def build(self):
		self.init_paths()
		self.post_init()

		self.update_sources()
		self.update()

		self.info()

		self.patch()

		if self.jenkins:
			self.build_zmq()

		if not self.export_only:
			self.compile()
			self.compile_post()

			if not self.mode_developer:
				self.exporter()

			if self.use_package:
				if self.mode_developer:
					sys.stdout.write("Package generation is disabled in 'Developer' mode.\n")
				else:
					releaeSubdir, releasePackage = self.package()
					if self.upload not in {'off'}:
						self.upload(releaeSubdir, releasePackage)

					if self.use_archive and hasattr(self, 'package_archive'):
						releaeSubdir, releasePackage = self.package_archive()
						if self.upload not in {'off'}:
							self.upload(releaeSubdir, releasePackage)


	def upload(self, subdir, filepath):
		if self.use_package_upload == 'http':
			import requests

			try:
				from configparser import RawConfigParser
			except:
				from ConfigParser import RawConfigParser

			config = RawConfigParser()
			config.read(os.path.expanduser("~/.passwd"))

			data = {
				"password" : config.get('cgdo.ru', 'upload_password'),
				"subdir"   : subdir,
			}

			files = {
				"file" : open(filepath, "rb"),
			}

			proxies = {}
			if self.use_proxy:
				proxies = {
					"http"  : self.use_proxy,
					"https" : self.use_proxy,
				}

			sys.stdout.write("Uploading package '%s' to '%s'...\n" % (filepath, subdir))
			requests.post("http://cgdo.ru/upload", files=files, data=data, proxies=proxies)

		elif self.use_package_upload == 'ftp':
			try:
				from configparser import ConfigParser
			except:
				from ConfigParser import ConfigParser

			config = ConfigParser()
			config.read(os.path.expanduser("~/.passwd"))

			now = datetime.datetime.now()
			subdir = now.strftime("%Y%m%d")

			cmd = None

			if sys.platform == 'win32':
				ftpScriptFilepath = os.path.join(tempfile.gettempdir(), "blender_for_vray_upload.txt")

				with open(ftpScriptFilepath, 'w') as f:
					f.write('option batch abort\n')
					f.write('option confirm off\n')
					f.write('open ftp://%s:%s@%s -rawsettings ProxyMethod=%s ProxyHost=%s ProxyPort=%s\n' % (
						config.get('nightlies.ftp', 'user'),
						config.get('nightlies.ftp', 'pass'),
						config.get('nightlies.ftp', 'host'),
						config.get('nightlies.ftp', 'proxy_type'),
						config.get('nightlies.ftp', 'proxy_host'),
						config.get('nightlies.ftp', 'proxy_port'),
					))
					f.write('option transfer binary\n')
					f.write('put %s /%s/\n' % (filepath, subdir))
					f.write('exit\n')
					f.write('\n')

				cmd = ['winscp']
				cmd.append('/passive')
				cmd.append('/script="%s"' % ftpScriptFilepath)

				if not self.mode_test:
					os.system(' '.join(cmd))

			else:
				cmd = ['curl']
				cmd.append('--no-epsv')
				if self.use_proxy:
					cmd.append('--proxy')
					cmd.append(self.use_proxy)
				cmd.append('--user')
				cmd.append('%s:%s' % (
					config.get('nightlies.ftp', 'user'),
					config.get('nightlies.ftp', 'pass'),
				))
				cmd.append('--upload-file')
				cmd.append(filepath)
				cmd.append('ftp://%s/%s/' % (
					config.get('nightlies.ftp', 'host'),
					subdir,
				))

				if not self.mode_test:
					subprocess.call(cmd)

			if self.mode_test:
				print(' '.join(cmd))


	def write_buildinfo(self, buildDir):
		import datetime
		now = datetime.datetime.now()

		lines = []
		lines.append('#define BUILD_COMMIT_TIMESTAMP 0')
		lines.append('#define BUILD_BRANCH "%s"' % (self.use_github_branch))
		lines.append('#define BUILD_HASH "%s"' % (self.revision[:7]))
		lines.append('#define BUILD_DATE "%s"' % (now.strftime("%d %b %Y")))
		lines.append('#define BUILD_TIME "%s"' % (now.strftime("%H:%M:%S")))
		lines.append('')

		buildInfoText = '\n'.join(lines)

		sys.stdout.write('Manul buildinfo.h content:\n%s\n' % buildInfoText)
		sys.stdout.flush()

		buildinfoTxt = os.path.join(buildDir, "source", "creator", "buildinfo.h")
		with open(buildinfoTxt, 'w') as buildinfo:
			buildinfo.write(buildInfoText)
