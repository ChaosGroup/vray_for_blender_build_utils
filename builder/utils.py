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


import getpass
import os
import platform
import re
import socket
import sys
import subprocess
import shutil


VERSION  = "2.61"
REVISION = "svn"

WIN = "windows"
LNX = "linux"
MAC = "macos"


def get_host_os():
	if sys.platform == "win32":
		return WIN
	elif sys.platform.find("linux") != -1:
		return LNX
	elif sys.platform == "darwin":
		return MAC

	sys.stderr.write("Unknown platform!\n")
	sys.exit(2)


def get_host_architecture():
	arch = 'x86' if platform.architecture()[0] == '32bit' else 'x86_64'

	if get_host_os() == "macos":
		arch = 'x86' if subprocess.check_output(['uname', '-p']) == 'i386' else 'x86_64'

	return arch


def get_hostname():
	return socket.gethostname()


def get_username():
	return getpass.getuser()


def path_basename(path):
	"""
	  Returns path's last dir
	"""
	if path.endswith(os.sep):
		path = path[:-1]

	return os.path.basename(path)


def path_create(path):
	if not os.path.exists(path):
		sys.stdout.write("Directory (%s) doesn\'t exist! Trying to create...\n" % (path))
		os.makedirs(path)


def path_expand(path):
	"""
	  Expands some special chars to real values
	"""
	if path.startswith('~'):
		path = os.path.expanduser(path)

	elif not path.startswith('/'):
		path = os.path.abspath(path)

	return path


def path_slashify(path):
	"""
	  Only for Windows
	"""
	if get_host_os() != WIN:
		return path

	path = os.path.normpath(path)
	path = path.replace('\\','\\\\')

	return path


def path_join(*args):
	"""
	  Joins path components for sure that
	  Windows paths will contain double back-slashes
	"""
	path = os.path.join(*args)

	if get_host_os() == WIN:
		path = path_slashify(path)

	return path


def pathExpand(path):
	path = os.path.expanduser(path)

	if path.startswith("./"):
		path = os.path.normpath(os.path.join(os.getcwd(), path))

	if get_host_os() != WIN:
		if not path.startswith("/"):
			path = os.path.normpath(os.path.join(os.getcwd(), path))

	return path


def which(program):
	"""
	  Returns full path of "program" or None
	"""

	def is_exe(fpath):
		return os.path.exists(fpath) and os.access(fpath, os.X_OK)

	fpath, fname = os.path.split(program)
	if fpath:
		if is_exe(program):
			return program
	else:
		for path in os.environ["PATH"].split(os.pathsep):
			exe_file = path_join(path, program)
			if is_exe(exe_file):
				return exe_file

	return None


def find_cmd_from_git(cmd):
	env_paths = os.getenv('PATH').split(';')

	for path in env_paths:
		if path.find('Git') == -1 and path.find('cmd') == -1:
			continue

		full_path = os.path.normpath(path_join(path, "..", "bin", cmd))
		if not os.path.exists(full_path):
			continue

		sys.stdout.write("Using \"%s\" from Git (%s)\n" % (cmd, full_path))

		return full_path

	return None


def find_makensis():
	common_paths = [
		path_join("C:", "Program Files",       "NSIS", "makensis.exe"),
		path_join("C:", "Program Files (x86)", "NSIS", "makensis.exe"),
	]

	for path in common_paths:
		if os.path.exists(path):
			return path

	# Try to find patch.exe in %PATH%
	if which("makensis.exe") is not None:
		return "makensis.exe"

	sys.stderr.write("Fatal error!\n")
	sys.stderr.write("makensis.exe command not found!!\n")
	sys.exit(2)


def find_command(cmd):
	if get_host_os() == WIN:
		cmd_exe = cmd+".exe"

		# Try to use patch.exe from Git installation
		cmd_exe = find_cmd_from_git(cmd_exe)
		if cmd_exe is not None:
			return '"%s"' % (cmd_exe)

		# Try to find patch.exe in %PATH%
		if which(cmd_exe) is not None:
			return cmd_exe

		# Try to find patch in Git installation
		# without using environment variables
		git_common_paths = [
			path_join("C:", "Program Files", "Git", "bin", cmd_exe),
			path_join("C:", "Program Files (x86)", "Git", "bin", cmd_exe),
		]

		for path in git_common_paths:
			if os.path.exists(path):
				return '"%s"' % (path)

	else:
		if which(cmd) is not None:
			return cmd

	sys.stderr.write("Fatal error!\n")
	sys.stderr.write("'%s' command not found!!\n" % cmd)
	sys.exit(2)


def find_patch():
	return find_command("patch")


def notify(title, message):
	if get_host_os() == LNX:
		if which("notify-send") is None:
			return
		os.system("notify-send \"%s\" \"%s\"" % (title, message))


def create_desktop_file(filepath = "/usr/share/applications/vrayblender.desktop",
						name     = "V-Ray/Blender",
						execpath = "blender",
						iconpath = "blender.svg"):
	"""
	  Creates Freedesktop .desktop file
	"""
	ofile= open(filepath, 'w')
	ofile.write("[Desktop Entry]\n")
	ofile.write("Name=%s\n" % (name))
	ofile.write("Exec=%s\n" % (execpath))
	ofile.write("Icon=%s\n" % (iconpath))
	ofile.write("Terminal=true\n")
	ofile.write("Type=Application\n")
	ofile.write("Categories=Graphics;3DGraphics;\n")
	ofile.write("StartupNotify=false\n")
	ofile.write("MimeType=application/x-blender;\n")
	ofile.close()


def _get_cmd_output(cmd, workDir=None):
	pwd = os.getcwd()
	if workDir:
		os.chdir(workDir)

	res = "None"
	if hasattr(subprocess, "check_output"):
		res = subprocess.check_output(cmd)
	else:
		res = subprocess.Popen(cmd, stdout=subprocess.PIPE).communicate()[0]
	res = res.decode().strip(" \n\r\t")

	if workDir:
		os.chdir(pwd)

	return res


def get_svn_revision(svn_root):
	git_rev = ['git', 'rev-parse', '--short', 'HEAD']
	b_rev   = ['git', 'rev-parse', '--short', 'github/master']
	git_cnt = ['git', 'rev-list',  '--count', 'HEAD']

	rev = _get_cmd_output(git_rev, svn_root)
	brev = _get_cmd_output(b_rev, svn_root)
	cnt = _get_cmd_output(git_cnt, svn_root)

	return rev, brev, cnt


def get_blender_version(root_dir):
	BKE_blender_h_path = path_join(root_dir, "source", "blender", "blenkernel", "BKE_blender.h")
	if not os.path.exists(BKE_blender_h_path):
		return VERSION

	BKE_blender_h = open(BKE_blender_h_path,'r').readlines()

	ver     = VERSION

	verMaj  = "2"
	verMin  = "72"
	verSub  = "1"
	verChar = ""

	def _get_define_value(l):
		l = l.strip().replace('\t', ' ')
		return l.split(' ')[-1].strip()

	for line in BKE_blender_h:
		if line.find("BLENDER_VERSION ") != -1:
			version_number = _get_define_value(line)
			verMaj = version_number[:1]
			verMin = version_number[1:]
			ver = verMaj + "." + verMin
		elif line.find("BLENDER_SUBVERSION") != -1:
			verSub = _get_define_value(line)
		elif line.find("BLENDER_VERSION_CHAR") != -1:
			verChar = _get_define_value(line)
			if len(verChar) > 1:
				verChar = ""

	return (ver, verMaj, verMin, verSub, verChar)


def get_linux_distribution():
	info = {}

	lsb_release = "/etc/lsb-release"
	if os.path.exists(lsb_release):
		with open(lsb_release, 'r') as lsbFile:
			for line in lsbFile.readlines():
				values = line.strip().split('=')
				if len(values) == 2:
					if values[0] == 'DISTRIB_ID':
						info['long_name']  = values[1]
						info['short_name'] = values[1].replace(' ','_')

					elif values[0] == 'DISTRIB_RELEASE':
						info['version'] = values[1]

	dist_info = platform.dist()
	if 'long_name' not in info:
		info['long_name']  = dist_info[0]
	if 'short_name' not in info:
		info['short_name'] = dist_info[0].replace(' ','_')
	if 'version' not in info:
		info['version']    = dist_info[1]

	for k in info:
		info[k] = info[k].strip().lower()

	if info['long_name'].find('Calculate Linux') != -1:
		info['short_name'] = 'Calculate'

	if info['long_name'].find('arch') != -1:
		info['short_name'] = 'archlinux'
		info['version']    = ''

	return info


def python_get_suffix(path, version):
	for s in ('m', 'mu', 'd', 'dmu'):
		if os.path.exists("%s%s%s" % (path,version,s)):
			return s
	return ""


def remove_directory(path):
	# Don't know why, but when deleting from python
	# on Windows it fails to delete '.git' direcotry,
	# so using shell command
	if get_host_os() == WIN:
		os.system("rmdir /Q /S %s" % path)
		# Well yes, on Windows one remove is not enough...
		if os.path.exists(path):
			os.system("rmdir /Q /S %s" % path)
	else:
		shutil.rmtree(path)


def move_directory(src, dst):
	if get_host_os() == WIN:
		os.system('move /Y "%s" "%s"' % (src, dst))
	else:
		shutil.move(src, dst)


def GetInstallDirName(self):
	branchID = ""
	if self.add_branch_name:
		branchID = "-%s" % self.use_github_branch.split("/")[-1]

	version  = self.version
	project  = self.project
	nCommits = self.commits
	arch     = self.build_arch

	params = {
		'project'  : self.project,
		'version'  : "-%s" % self.version,
		'nCommits' : "-%s" % self.commits,
		'hash'     : "-%s" % self.revision,
		'bhash'    : "-%s" % self.brev,
		'arch'     : "-%s" % self.build_arch,
		'branch'   : branchID,
	}

	if self.use_blender_hash:
		params.update({
			'version' : "-%s" % self.use_blender_hash,
			'hash'    : "",
		})

	if self.teamcity:
		params.update({
			'bhash' : "",
			'nCommits' : "",
		})

	return "{project}{version}{nCommits}{bhash}{hash}{arch}{branch}".format(**params)


def GetPackageName(self, ext=None):
	def _get_host_package_type():
		if get_host_os() == WIN:
			return "exe"
		else:
			return "tar.bz2"

	os = get_host_os()
	if os == 'linux':
		os = "%s%s" % (get_linux_distribution()['short_name'], get_linux_distribution()['version'])

	params = {
		'build_name' : GetInstallDirName(self),
		'os' : os,
		'ext' : ext if ext else _get_host_package_type(),
	}

	return "{build_name}-{os}.{ext}".format(**params)


def GetCmakeOnOff(val):
	return "ON" if val else "OFF"


def GenCGRInstaller(self, installer_path, InstallerDir="H:/devel/vrayblender/cgr_installer"):
	def unix_slashes(path):
		p = os.path.normpath(path.replace("\\", "/"))
		return p

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

		# Release or nighlty
		tmpl = tmpl.replace("${IS_RELEASE_BUILD}", "%i" % (self.build_mode == 'release'))

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
	packer.append('-wmstr="ad6347ff-db11-47a5-9324-3d7bca5a94ac"')
	packer.append('-wmval="7d263cec-e754-456b-8d5c-1ffecdd796d7"')

	if self.mode_test:
		print(" ".join(packer))
	else:
		subprocess.call(packer)
