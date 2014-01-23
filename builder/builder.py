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
import tempfile
import subprocess
import datetime

import utils


OFFICIAL_REPO = "http://git.blender.org/blender.git"
GITHUB_REPO   = "https://github.com/bdancer/blender-for-vray.git"


class Builder:
	"""
	  A generic build class.
	"""

	project        = "vrayblender"
	version        = utils.VERSION
	revision       = utils.REVISION

	# Directories
	dir_build      = utils.path_join(os.getcwd(), "build")
	dir_install    = utils.path_join(os.getcwd(), "install")
	dir_release    = utils.path_join(os.getcwd(), "release")
	dir_source     = ""

	dir_blender     = ""
	dir_blender_svn = ""

	# Installation diractory name
	dir_install_name = "vrayblender"
	dir_install_path = utils.path_join(dir_install, dir_install_name)

	# Build archive for Mac and Linux
	# or NSIS installer for Windows
	generate_package = False
	generate_desktop = False
	generate_docs    = False

	# Test mode - just print messages, does nothing
	mode_test      = True

	# Special mode used only by me =)
	mode_developer = False

	# Debug output of the script
	mode_debug     = False

	# Add V-Ray/Blender patches
	add_patches    = True

	# Add V-Ray/Blender datafiles
	add_datafiles  = True

	# Add patches from "extra" directory
	add_extra      = False

	# Add themes from "themes" directory
	add_themes     = False

	# Host info
	host_os        = utils.get_host_os()
	host_arch      = utils.get_host_architecture()
	host_name      = utils.get_hostname()
	host_username  = utils.get_username()
	host_linux     = utils.get_linux_distribution()

	# Install dependencies
	install_deps   = False
	build_deps     = False
	use_build_deps = False

	# Update sources
	update_blender = True
	update_patch   = True

	# Blender option
	use_debug      = False
	use_openmp     = True
	use_collada    = False
	use_sys_python = True
	use_sys_ffmpeg = True

	# Build settings
	build_arch          = host_arch
	build_threads       = 4
	build_optimize      = False
	build_optimize_type = "INTEL"
	build_clean         = False
	build_release       = False
	build_upload        = False
	checkout_revision   = None
	use_env_msvc        = False

	# user-config.py file path
	user_config         = ""

	# Use user defined user-config.py
	user_user_config    = ""

	# Max OS X specific
	osx_sdk             = "10.6"

	with_cycles         = False
	with_tracker        = False
	with_cuda           = False
	cuda_gpu            = "sm_21"
	with_osl            = False
	with_player         = False
	with_ge             = False

	use_proxy           = None

	use_github_repo     = None
	use_github_branch   = None

	def __init__(self, params):
		if not params:
			sys.stdout.write("Params are empty - using defaults...\n")

		for param in params:
			setattr(self, param, params[param])

		if self.mode_debug:
			for param in params:
				print("%s => %s" % (param, params[param]))
			print("")

		if not self.dir_source:
			sys.stderr.write("Fatal error!\n")
			sys.stderr.write("Source directory not specified!\n")
			sys.exit(2)

		if not (self.add_patches or self.use_github_repo):
			self.project = "blender"


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


	def update_sources(self):
		"""
		  Getting/updating sources
		"""

		def genBuildInfo():
			with open(os.path.join(self.dir_blender, "source", "creator", "buildinfo.h"), 'w') as f:
				now = datetime.datetime.now()

				f.write('#define BUILD_HASH "%s"\n' % utils.get_svn_revision(self.dir_blender_svn))
				f.write('#define BUILD_CHANGE ""\n')
				f.write('#define BUILD_BRANCH "dev/vray_for_blender"\n')
				f.write('#define BUILD_DATE "%s"\n' % now.strftime("%Y-%m-%d"))
				f.write('#define BUILD_TIME "%s"\n' % now.strftime("%H:%M:%S"))
				f.write('\n')

		def exportSources():
			sys.stdout.write("Exporting sources...\n")
			if self.mode_test:
				return

			if os.path.exists(self.dir_blender):
				utils.remove_directory(self.dir_blender)

			# Copy full tree to have proper build info.
			shutil.copytree(self.dir_blender_svn, self.dir_blender)

			if self.use_github_repo:
				os.chdir(self.dir_blender)
				os.system("git checkout -b {branch} github/{branch}".format(branch=self.use_github_branch))

			if self.checkout_revision is not None:
				os.chdir(self.dir_blender)
				os.system("git checkout %s" % self.checkout_revision)

		# Update Blender sources
		if self.update_blender:
			if os.path.exists(self.dir_blender):
				sys.stdout.write("Removing exported sources...\n")
				if not self.mode_test:
					utils.remove_directory(self.dir_blender)

			if not os.path.exists(self.dir_blender_svn):
				sys.stdout.write("Obtaining Blender sources...\n")
				if not self.mode_test:
					os.chdir(self.dir_source)

					# Obtain sources
					if self.use_github_repo:
						os.system("git clone %s blender" % GITHUB_REPO)

						# Now set origin to Blender's git and additional github remote
						# This is needed for proper submodules init
						#
						os.chdir(self.dir_blender)
						os.system("git remote set-url origin %s" % OFFICIAL_REPO)
						os.system("git remote add github %s" % GITHUB_REPO)
						os.system("git remote update")
						os.system("git pull --rebase")
					else:
						os.system("git clone %s" % OFFICIAL_REPO)

					os.chdir(self.dir_blender)
					os.system("git submodule update --init --recursive")
					os.system("git submodule foreach git checkout master")
					os.system("git submodule foreach git pull --rebase origin master")

					os.chdir(self.dir_source)
					# Move "blender" to "blender-git"
					utils.move_directory(self.dir_blender, self.dir_blender_svn)

			else:
				sys.stdout.write("Updating Blender sources...\n")
				if not self.mode_test:
					os.chdir(self.dir_blender_svn)

					# Update sources
					os.system("git pull --rebase")
					os.system("git submodule foreach git pull --rebase origin master")

			exportSources()

			# Update Blender libs
			lib_dir = None
			svn_cmd = None
			if self.host_os != utils.LNX:
				if self.host_os == utils.WIN:
					lib_dir = utils.path_join(self.dir_source, "lib", "windows")
					svn_cmd = "svn checkout https://svn.blender.org/svnroot/bf-blender/trunk/lib/windows lib/windows"
					if self.host_arch == "x86_64":
						lib_dir = utils.path_join(self.dir_source, "lib", "win64")
						svn_cmd = "svn checkout https://svn.blender.org/svnroot/bf-blender/trunk/lib/win64 lib/win64"
				elif self.host_os == utils.MAC:
					lib_dir = utils.path_join(self.dir_source, "lib", "darwin-9.x.universal")
					svn_cmd = "svn checkout https://svn.blender.org/svnroot/bf-blender/trunk/lib/darwin-9.x.universal lib/darwin-9.x.universal"

				if not os.path.exists(lib_dir):
					sys.stdout.write("Getting \"lib\" data...\n")
					if not self.mode_test:
						os.chdir(self.dir_source)
						os.system(svn_cmd)
				else:
					sys.stdout.write("Updating \"lib\" data...\n")
					if not self.mode_test:
						os.chdir(lib_dir)
						os.system("svn update")

		# Update V-Ray/Blender patchset
		if self.update_patch and not self.mode_developer:
			vb25_patch = utils.path_join(self.dir_source, "vb25-patch")

			if os.path.exists(vb25_patch):
				sys.stdout.write("Updating V-Ray/Blender patches...\n")
				if not self.mode_test:
					os.chdir(vb25_patch)
					os.system("git pull")
			else:
				sys.stdout.write("Getting V-Ray/Blender patches...\n")
				if not self.mode_test:
					os.chdir(self.dir_source)
					os.system("git clone git://github.com/bdancer/vb25-patch.git")


	def update(self):
		self.revision = utils.get_svn_revision(self.dir_blender_svn)
		self.version  = utils.get_blender_version(self.dir_blender_svn)

		if self.build_release:
			self.dir_install_name = "%s-%s-%s-%s" % (self.project, self.version, self.revision, self.build_arch)
		else:
			self.dir_install_name = self.project

		self.dir_install_path = utils.path_join(self.dir_install, self.dir_install_name)


	def patch(self):
		patch_dir = utils.path_join(self.dir_source, "vb25-patch")

		if not os.path.exists(patch_dir):
			sys.stderr.write("Fatal error!\n")
			sys.stderr.write("Patch directory (%s) not found!\n" % (patch_dir))
			sys.exit(2)

		if not os.path.exists(utils.path_join(patch_dir, "patch")):
			sys.stderr.write("Fatal error!\n")
			sys.stderr.write("Something wrong happened! Patch directory is incomplete!\n")
			sys.exit(2)

		# Blender clean exported souces
		blender_dir = utils.path_join(self.dir_source, "blender")
		if self.add_patches or self.add_extra:
			if not os.path.exists(patch_dir):
				sys.stderr.write("Fatal error!\n")
				sys.stderr.write("Exported Blender sources (%s) not found!\n" % (blender_dir))
				sys.exit(2)

			patch_cmd  = utils.find_patch()

			# Apply V-Ray/Blender patches
			if self.add_patches:
				sys.stdout.write("Adding V-Ray/Blender patches...\n")

				cmd = "%s -Np1 -i %s" % (patch_cmd, utils.path_join(patch_dir, "patch", "vray_for_blender.patch"))

				# Patching Blender sources
				sys.stdout.write("Patching sources...\n")
				sys.stdout.write("Patch command: %s\n" % (cmd))
				if not self.mode_test:
					os.chdir(blender_dir)
					os.system(cmd)

		# Apply extra patches
		if self.add_extra:
			extra_dir = path_join(patch_dir, "patch", "extra")

			patches   = []
			for f in os.listdir(extra_dir):
				if f.endswith(".patch"):
					patches.append(utils.path_join(extra_dir), f)

			if not self.mode_test:
				os.chdir(blender_dir)
				for patch_file in patches:
					cmd = "%s -Np0 -i %s" % (patch_cmd, patch_file)
					os.system(cmd)

		# Add datafiles: splash, default scene etc
		if self.add_datafiles:
			sys.stdout.write("Adding datafiles...\n")

			datafiles_path = utils.path_join(blender_dir, "release", "datafiles")

			# Change splash
			splash_filename = "splash.png"
			splash_path_src = utils.path_join(patch_dir, "datafiles", splash_filename)
			splash_path_dst = utils.path_join(datafiles_path, splash_filename)

			if not self.mode_test:
				shutil.copyfile(splash_path_src, splash_path_dst)

				# Change icons
				for subdir in ["blender_icons16", "blender_icons32"]:
					icons_path_src = utils.path_join(patch_dir, "datafiles", subdir)
					icons_path_dst = utils.path_join(datafiles_path, subdir)

					shutil.rmtree(icons_path_dst)
					shutil.copytree(icons_path_src, icons_path_dst)


	def docs(self):
		if self.generate_docs:
			api_dir = utils.path_join(self.dir_install_path, "api")

			sys.stdout.write("Generating API documentation: %s\n" % (api_dir))

			if self.host_os != utils.LNX:
				sys.stdout.write("API documentation generation is not supported on this platform.\n")

			else:
				if not self.mode_test:
					sphinx_doc_gen = "doc/python_api/sphinx_doc_gen.py"

					# Create API directory
					os.system("mkdir -p %s" % api_dir)

					# Generate API docs
					os.chdir(self.dir_blender)
					os.system("%s -b -P %s" % (utils.path_join(self.dir_install_path, "blender"), sphinx_doc_gen))
					os.system("sphinx-build doc/python_api/sphinx-in %s" % api_dir)


	def post_init(self):
		"""
		  Override this method in subclass.
		"""
		pass


	def init_paths(self):
		if self.generate_package:
			if not self.mode_test:
				utils.path_create(self.dir_release)

		self.dir_build        = utils.path_slashify(self.dir_build)
		self.dir_source       = utils.path_slashify(self.dir_source)
		self.dir_install_path = utils.path_slashify(self.dir_install_path)

		self.dir_blender      = utils.path_join(self.dir_source, "blender")
		self.dir_blender_svn  = utils.path_join(self.dir_source, "blender-git")
		self.user_config      = utils.path_join(self.dir_blender, "user-config.py")

		if self.user_user_config:
			self.user_user_config = utils.pathExpand(self.user_user_config)

		if os.path.exists(self.dir_build):
			shutil.rmtree(self.dir_build)


	def config(self):
		"""
		  Override this method in subclass.
		"""
		sys.stderr.write("Base class method called: config() This souldn't happen.\n")


	def compile(self):
		compileCmd = [sys.executable]
		compileCmd.append("scons/scons.py")

		if not self.build_clean:
			compileCmd.append("--implicit-deps-unchanged")
			compileCmd.append("--max-drift=1")

		if self.use_env_msvc:
			compileCmd.append(r'env="PATH:%PATH%,INCLUDE:%INCLUDE%,LIB:%LIB%"')

		cleanCmd = [sys.executable]
		cleanCmd.append("scons/scons.py")
		cleanCmd.append("clean")

		if not self.mode_test:
			os.chdir(self.dir_blender)

			if self.build_clean:
				sys.stdout.write("Calling: %s\n" % (" ".join(cleanCmd)))
				subprocess.call(cleanCmd)

			sys.stdout.write("Calling: %s\n" % (" ".join(compileCmd)))
			res = subprocess.call(compileCmd)
			if not res == 0:
				sys.stderr.write("There was an error during the compilation!\n")
				sys.exit(1)

			if self.host_os == utils.WIN:
				shutil.copy(utils.path_join(self.dir_source, "vb25-patch", "non-gpl", self.build_arch, "vcomp90.dll"), self.dir_install_path)


	def exporter(self):
		"""
		  Add exporting script
		"""
		sys.stdout.write("Adding exporter...\n")

		scripts_path  = utils.path_join(self.dir_install, self.dir_install_name, self.version, "scripts", "startup")
		exporter_path = utils.path_join(scripts_path, "vb25")

		sys.stdout.write("  in: %s\n" % (scripts_path))

		if self.host_os == utils.MAC:
			scripts_path = utils.path_join(self.dir_install, self.dir_install_name, "blender.app", "Contents", "MacOS", self.version, "scripts", "startup")

		if not self.mode_test:
			if not os.path.exists(scripts_path):
				sys.stderr.write("Build failed! Can't add exporter!\n")
				return

			# Remove old
			if os.path.exists(exporter_path):
				utils.remove_directory(exporter_path)

			# Add new
			os.chdir(scripts_path)
			os.system("git clone --depth=1 git://github.com/bdancer/vb25.git")


	def package(self):
		"""
		  Override this method in subclass.
		"""
		sys.stderr.write("Base class method called: package() This souldn't happen.\n")


	def build(self):
		self.init_paths()
		self.post_init()

		self.update_sources()
		self.update()

		self.info()

		self.patch()
		self.config()
		self.compile()

		if not self.mode_developer:
			self.exporter()

		self.docs()

		if self.generate_package:
			if self.mode_developer:
				sys.stdout.write("Package generation is disabled in 'Developer' mode.\n")
			else:
				if self.build_release:
					releaeSubdir, releasePackage = self.package()
					if self.build_upload != 'off':
						self.upload(releaeSubdir, releasePackage)
				else:
					sys.stdout.write("Package generation is disabled in non-release mode.\n")


	def upload(self, subdir, filepath):
		if self.build_upload == 'http':
			import requests

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

		elif self.build_upload == 'ftp':
			from ConfigParser import RawConfigParser

			config = RawConfigParser()
			config.read(os.path.expanduser("~/.passwd"))

			curl = [utils.find_command("curl")]
			curl.append('--upload-file')
			curl.append(filepath)
			if self.use_proxy:
				curl.append('--proxy')
				curl.append(self.use_proxy)

			curl.append('--user')
			curl.append('%s:%s' % (config.get('chaosgroup.ftp', 'user'), config.get('chaosgroup.ftp', 'pass')))

			curl.append('ftp://%s/demo/%s' % (config.get('chaosgroup.ftp', 'host'), os.path.basename(filepath)))

			sys.stdout.write("Uploading package '%s' to '%s'...\n" % (filepath, subdir))
			sys.stdout.write("Command: %s\n" % (' '.join(curl)))
			if not self.mode_test:
				subprocess.call(curl)
