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
	b_rev   = ['git', 'rev-parse', '--short', 'master']
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
	long_info  = platform.linux_distribution()
	short_info = platform.dist()

	info = {}
	info['long_name']  = long_info[0].strip()
	info['short_name'] = short_info[0].lower().replace(' ','_').strip()
	info['version']    = short_info[1].strip()

	if info['long_name'].find('Calculate Linux') != -1:
		info['short_name'] = 'Calculate'

	if info['long_name'].find('arch') != -1:
		info['short_name'] = 'archlinux'

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

	return "{project}{version}{nCommits}{bhash}{hash}{arch}{branch}".format(**params)


def GetPackageName(self):
	def _get_host_package_type():
		if get_host_os() == WIN:
			return "exe"
		else:
			return "tar.bz2"

	os = get_host_os()
	if os == 'linux':
		os = get_linux_distribution()['short_name']

	params = {
		'build_name' : GetInstallDirName(self),
		'os' : os,
		'ext' : _get_host_package_type(),
	}

	return "{build_name}-{os}.{ext}".format(**params)


def GetCmakeOnOff(val):
	return "ON" if val else "OFF"
