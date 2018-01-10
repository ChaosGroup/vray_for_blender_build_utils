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
import stat
import sys
import subprocess
import shutil
import tempfile
import time

VERSION  = "2.61"
REVISION = "svn"

WIN = "windows"
LNX = "linux"
MAC = "macos"

install_package_ignores = [
	'vray.exe',      # ignore std from appsdk
	'vray.bin',      # ignore std from appsdk
]

# rename qt version to original name
appsdk_renames = {
	'vray_qt.dll': 'vray.dll',
	'libvray_qt.so': 'libvray.so',
	'libvray_qt.dylib': 'libvray.dylib',
}


def stdout_log(*args):
	sys.stdout.write(*args)
	sys.stdout.write('\n')
	sys.stdout.flush()


def stderr_log(*args):
	sys.stderr.write(*args)
	sys.stderr.write('\n')
	sys.stderr.flush()


def get_host_os():
	if sys.platform == "win32":
		return WIN
	elif sys.platform.find("linux") != -1:
		return LNX
	elif sys.platform == "darwin":
		return MAC

	sys.stderr.write("Unknown platform!\n")
	sys.exit(2)


def get_default_install_path():
	if get_host_os() == WIN:
		return "C:/Program Files/Chaos Group/"
	elif get_host_os() == MAC:
		return "/Applications/ChaosGroup/"
	else:
		return "/usr/ChaosGroup/"


def exec_and_log(cmd, tag="", exit=False):
	tag = tag if tag != '' else 'CMD: '
	sys.stdout.write('%s: [%s] cwd(%s) \n' % (tag, cmd, os.getcwd()))
	sys.stdout.flush()
	if 0 != os.system(cmd):
		sys.stderr.write('%s: command failed! [%s]\n' % (tag, cmd))
		sys.stderr.flush()
		if exit:
			sys.exit(2)


def get_repo(repo_url, branch='master', target_dir=None, target_name=None, submodules=[]):
	"""
	This will clone the repo in CWD. If target_dir != None it will copy 
	the sources to target_dir"""

	sys.stdout.write("Repo [%s]\n" % repo_url)
	sys.stdout.flush()

	repo_name = target_name if target_name is not None else os.path.basename(repo_url)
	cwd = os.getcwd()
	clone_dir = os.path.join(cwd, repo_name)

	git_cmds = []
	dumpAndExec = lambda cmd: exec_and_log(cmd, 'GIT', True)

	repo_dir_exists = os.path.exists(clone_dir)

	if repo_dir_exists:
		existing_url = get_git_remote_url(clone_dir)
		sys.stderr.write('target_name "%s" exists [%s]\n' % (repo_name, clone_dir))
		sys.stderr.write('\trequested url:[%s]\n\tpresent url:[%s]\n' % (repo_url, existing_url))
		sys.stderr.flush()
		if existing_url != repo_url:
			sys.stderr.write("Urls are different - removing [%s]\n" % clone_dir)
			sys.stderr.flush()
			remove_directory(clone_dir)
			repo_dir_exists = False

	if not repo_dir_exists:
		get_cmd = ""
		if target_name and not target_dir:
			# just rename clone
			dumpAndExec("git clone %s %s" % (repo_url, target_name))
		else:
			dumpAndExec("git clone %s" % repo_url)

	os.chdir(clone_dir)
	git_cmds = git_cmds + [
		"git fetch origin",
		"git clean -ffd",
		"git checkout -f origin/%s" % branch,
		"git submodule foreach --recursive git clean -ffd",
		"git clean -ffd",
	]

	for module in submodules:
		git_cmds.append("git submodule update --force --init --recursive %s" % module)

	for cmd in git_cmds:
		dumpAndExec(cmd)

	if target_dir:
		to_dir = os.path.join(target_dir, repo_name)
		if target_name:
			to_dir = os.path.join(target_dir, target_name)

		sys.stdout.write("Exporting sources %s -> %s\n" % (clone_dir, to_dir))
		sys.stdout.flush()

		if os.path.exists(to_dir):
			remove_directory(to_dir)

		shutil.copytree(clone_dir, to_dir)

	os.chdir(cwd)


def get_host_architecture():
	arch = 'x86' if platform.architecture()[0] == '32bit' else 'x86_64'

	if get_host_os() == "macos":
		arch = 'x86' if subprocess.check_output(['uname', '-p']) == 'i386' else 'x86_64'

	if get_host_os() == WIN:
		if (arch == 'x86_64') != platform.machine().endswith('64'):
			sys.stderr.write('Missmatch in platform.architecture() and platform.machine().\n')
			sys.stderr.write('This is probably 32 bit python on 64 bit os.\n')
			sys.stderr.flush()
			arch = 'x86_64' if platform.machine().endswith('64') else 'x86'

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


def dir_contents_recursive(path):
	res = []
	for dirpath, dirnames, filenames in os.walk(path):
		for dir_name in dirnames:
			res.append(os.path.join(dirpath, dir_name))
		for file_name in filenames:
			res.append(os.path.join(dirpath, file_name))
	return res


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


def which(program, add_ext=False):
	"""
	  Returns full path of "program" or None, if it fails will print where it tried
	"""

	def is_exe(fpath):
		return os.path.exists(fpath) and os.access(fpath, os.X_OK)

	# log what we tried if we fail
	log = []

	result = None

	fpath, fname = os.path.split(program)
	if fpath:
		if is_exe(program):
			return program
	else:
		for path in os.environ["PATH"].split(os.pathsep):
			exe_file = path_join(path, program)
			log.append('Checking if path [%s] is path for [%s] ... ' % (exe_file, fname))
			if is_exe(exe_file):
				log[-1] = log[-1] + 'yes!\n';
				result = exe_file
				break
			log[-1] = log[-1] + 'no!\n'

		if get_host_os() == WIN and not add_ext:
			result = which('%s.exe' % program, True)

	if not result:
		for l in log:
			sys.stderr.write('%s\n' % l)
		sys.stderr.flush()

	return result


def find_cmd_from_git(cmd):
	env_paths = os.getenv('PATH').split(ENV_PATH_SEP)

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


def _get_cmd_output_ex(cmd, workDir=None):
	logDir = workDir if workDir is not None else 'None(%s)' % os.getcwd()
	sys.stdout.write('Executing [%s] inside [%s]\n' % (' '.join(cmd), logDir))
	sys.stdout.flush()
	pwd = os.getcwd()
	if workDir:
		os.chdir(workDir)

	res = "None"
	code = 0
	if hasattr(subprocess, "check_output"):
		try:
			res = subprocess.check_output(cmd)
		except subprocess.CalledProcessError as e:
			code = e.returncode
			res = e.output
	else:
		proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)
		res = proc.communicate()[0]
		code = proc.returncode
	res = res.decode().strip(" \n\r\t")

	if workDir:
		os.chdir(pwd)

	return {'code': code, 'output': res}


def _get_cmd_output(cmd, workDir=None):
	return _get_cmd_output_ex(cmd, workDir)['output']


def get_git_remote_url(root):
	get_remote = ['git', 'remote', '-v']
	lines = _get_cmd_output(get_remote, workDir=root).split('\n')
	sys.stdout.write('get_git_remote_url(%s):\n%s\n\n' % (root, lines))
	sys.stdout.flush()
	for l in lines:
		match = re.match(r'(\w+?)\s([^ ]+?)\s\((\w+?)\)', l)
		if match is not None:
			name, url, tp = match.groups()
			if name == 'origin':
				return url


def get_git_head_hash(root):
	git_rev = ['git', 'rev-parse', '--short', 'HEAD']
	return _get_cmd_output(git_rev, root)


def get_svn_revision(svn_root):
	b_rev   = ['git', 'rev-parse', '--short', 'github/master']
	git_cnt = ['git', 'rev-list',  '--count', 'HEAD']

	rev = get_git_head_hash(svn_root)
	brev = _get_cmd_output(b_rev, svn_root)
	cnt = _get_cmd_output(git_cnt, svn_root)

	return rev, brev, cnt


def get_blender_version(root_dir):
	BKE_blender_h_path = path_join(root_dir, "source", "blender", "blenkernel", "BKE_blender_version.h")
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


def delete_dir_contents(path):
	if not os.path.exists(path):
		stdout_log("Failed to clean_dir(%s), path does not exist" % path)
		return

	if not os.path.isdir(path):
		stdout_log("Failed to clean_dir(%s), path is not dir" % path)
		return

	stdout_log("delete_dir_contents(%s)" % path)

	def rmtree_onerror(func, path, exc_info):
		if os.path.islink(path):
			os.unlink(path)

	def _remove_readonly(fn, path, excinfo):
		# Handle read-only files and directories
		if fn is os.rmdir:
			os.chmod(path, stat.S_IWRITE)
			os.rmdir(path)
		elif fn is os.remove:
			os.lchmod(path, stat.S_IWRITE)
			os.remove(path)


	def force_remove_file_or_symlink(path):
		try:
			os.remove(path)
		except OSError:
			os.lchmod(path, stat.S_IWRITE)
			os.remove(path)


	# Code from shutil.rmtree()
	def is_regular_dir(path):
		try:
			mode = os.lstat(path).st_mode
		except os.error:
			mode = 0
		return stat.S_ISDIR(mode)


	for name in os.listdir(path):
		fullpath = os.path.join(path, name)
		if is_regular_dir(fullpath):
			shutil.rmtree(fullpath, onerror=_remove_readonly)
		else:
			force_remove_file_or_symlink(fullpath)


def remove_path(path):
	if not os.path.exists(path):
		stdout_log('remove_path(%s) but path does not exist' % path)
	if os.path.isdir(path):
		remove_directory(path)
	elif os.path.isfile(path):
		remove_file(path)
	elif os.path.islink(path):
		stdout_log("utils.remove_path(%s) -> unlink" % path)
		os.unlink(path)
	else:
		sys.stderr.write('Called utils.remove_path(%s), but it is not dir nor file!\n' % path)
		sys.stderr.flush()


def remove_file(path):
	sys.stdout.write('Called utils.remove_file(%s)\n' % path)
	sys.stdout.flush()
	os.remove(path)


def remove_directory(path):
	# Don't know why, but when deleting from python
	# on Windows it fails to delete '.git' direcotry,
	# so using shell command
	sys.stdout.write('Called utils.remove_directory(%s)\n' % path)
	sys.stdout.flush()
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

	if self.teamcity or self.jenkins:
		params.update({
			'bhash' : "",
			'nCommits' : "",
			'hash'     : "-%s" % self.revision[:7],
		})

	sys.stdout.write('GetInstallDirName params: \n%s\n' % str(params))
	sys.stdout.flush()

	return "{project}{version}{nCommits}{bhash}{hash}{arch}{branch}".format(**params)


def WritePackageInfo(self, packagePath):
	bInfo = os.path.join(packagePath, 'build-info.txt')
	sys.stdout.write('Writing build info in [%s]\n' % bInfo)
	sys.stdout.flush()
	if not os.path.isdir(packagePath):
		sys.stdout.write('Creating [%s]\n' % packagePath)
		sys.stdout.flush()
		path_create(packagePath)
	with open(bInfo, 'w+') as f:
		f.write('BLENDER_VERSION=%s\n' % self.version)
		f.write('BLENDER_HASH=%s\n' % self.revision)


def GetPackageName(self, ext=None):
	os = get_host_os()

	def _get_host_package_type():
		if os == WIN:
			return "exe"
		elif os == MAC:
			return 'dmg'
		else:
			return "bin"

	if os == LNX:
		os = "%s%s" % (get_linux_distribution()['short_name'], get_linux_distribution()['version'])

	params = {
		'build_name' : GetInstallDirName(self),
		'os' : os,
		'ext' : ext if ext else _get_host_package_type(),
	}

	return "{build_name}-{os}.{ext}".format(**params)


def GetCmakeOnOff(val):
	return "ON" if val else "OFF"


def unix_slashes(path):
	return os.path.normpath(path.replace("\\", "/"))


def mac_rewrite_link_file(executable, source, dest):
	"""For MAC OS only!
	Will change the default search path source @source to @dest for the given executable
	Will do the changes in temp file, and overwrite the existing then
	"""
	rename_cmd = ['install_name_tool', '-change', source, dest, executable]

	sys.stdout.write("[%s]\n" % ", ".join(rename_cmd))
	sys.stdout.flush()
	result = subprocess.call(rename_cmd)
	if result != 0:
		sys.stderr.write('rename_cmd failed\n')
		sys.stderr.flush()
		sys.exit(1)


def mac_rewrite_qt_links(binfile, relpath=''):
	"""For MAC OS only!
	Rewrites all links for QtGui and QtCore to @executable_path/relpath
	Returns paths to rewrote links
	"""
	items = []
	qt_find = ['otool', '-L', binfile]

	sys.stdout.write("[%s]\n" % ", ".join(qt_find))
	sys.stdout.flush()
	res = _get_cmd_output_ex(qt_find)
	if res['code'] != 0:
		sys.stderr.write('"%s" failed\n' % ' '.join(qt_find))
		sys.stderr.flush()
		sys.exit(1)

	links = res['output'].split('\n')

	for line in links:
		regExMatch = re.match(r'.*?(?:lib)?Qt5?(Core|Gui|Widgets)(?:.5.dylib)?\s?.*?', line)
		if regExMatch == None:
			continue

		qtLibFile = 'lib%s.dylib' % regExMatch.groups()[0]

		fullPath = os.path.join(os.path.dirname(binfile), relpath, qtLibFile)
		rename_path = os.path.join('@executable_path', relpath, qtLibFile)
		# items.append(fullPath)
		sys.stdout.write("Renaming qt lib : [%s]:\"%s\" -> \"%s\" [%s]\n" % (line, q_path, rename_path, fullPath))
		sys.stdout.flush()
		mac_rewrite_link_file(binfile, q_path, rename_path)

	return items


def prepare_appsdk(appsdk_path):
	host_os = get_host_os()
	for dirpath, dirnames, filenames in os.walk(appsdk_path):
		for file_name in filenames:
			file_path = os.path.join(dirpath, file_name)
			if file_name in install_package_ignores:
				os.remove(file_path)
				continue

			if file_name in appsdk_renames:
				dest = os.path.join(dirpath, appsdk_renames[file_name])
				if os.path.exists(dest):
					os.unlink(dest)
				os.rename(file_path, dest)
				file_path = dest

			if host_os == MAC:
				mac_rewrite_qt_links(file_path)


def get_zmq_build_items(self, appsdkFile):
	host_os = get_host_os()

	extension = '.exe' if host_os == WIN else ''
	sub_dir_template = "install/vrayserverzmq/V-Ray/VRayZmqServer/VRayZmqServer%s" % extension

	items = []

	zmq_build_path = ''
	if self.jenkins:
		zmq_build_path = os.path.join(self.dir_install, '..', 'vrayserverzmq', 'V-Ray', 'VRayZmqServer', 'VRayZmqServer%s' % extension)

	if host_os == WIN:
		if not os.path.exists(zmq_build_path):
			zmq_build_path = "H:/%s" % sub_dir_template
		items = [zmq_build_path]
	elif host_os == LNX:
		if not os.path.exists(zmq_build_path):
			zmq_build_path = "/home/teamcity/%s" % sub_dir_template
		# lets try in our home dir
		if not os.path.exists(zmq_build_path):
			zmq_build_path = os.path.expanduser("~/%s" % sub_dir_template)
		items = [zmq_build_path]
	elif host_os == MAC:
		# copy file, edit search path for appsdk lib and add to installation
		if not os.path.exists(zmq_build_path):
			zmq_build_path = "/Users/andreiizrantsev/%s" % sub_dir_template
		# lets try in our home dir
		if not os.path.exists(zmq_build_path):
			zmq_build_path = os.path.expanduser("~/%s" % sub_dir_template)

		# we will rename appsdk and Qt to point to appsdk folder
		zmq_temp = "%s/VRayZmqServer" % tempfile.gettempdir()
		if os.path.exists(zmq_temp):
			remove_file(zmq_temp)
		shutil.copyfile(zmq_build_path, zmq_temp)

		# rewrite Qt links
		items = items + mac_rewrite_qt_links(zmq_temp, 'appsdk')
		mac_rewrite_link_file(zmq_temp, appsdkFile, '@executable_path/appsdk/%s' % appsdkFile)
		items.append(zmq_temp)

	for item in items:
		if not os.path.exists(item):
			sys.stderr.write("Could not find [%s]\n" % item)
			sys.stderr.flush()
			sys.exit(1)

	return items


def generateMacInstaller(self, InstallerDir, tmplFinal, installer_path, short_title, long_title):
	root_tmp = tempfile.mkdtemp()
	target_name = os.path.basename(installer_path).replace('.dmg', '')
	bin_path = installer_path.replace('.dmg', '.bin')

	sys.stdout.write('Macos installer tmp wd %s\n' % root_tmp)
	sys.stdout.flush()

	sys.stdout.write('Step 1, create uninstaller/installer plist files\n')
	sys.stdout.flush()
	os.mkdir(os.path.join(root_tmp, 'installer'))
	os.mkdir(os.path.join(root_tmp, 'uninstaller'))
	plist_install = os.path.join(root_tmp, 'installer', 'Info.plist')
	plist_uninstall = os.path.join(root_tmp, 'uninstaller', 'Info.plist')

	plist_original = open('%s/macos/osx_installer/Info.plist.in' % InstallerDir, 'r').read()
	plist_original = plist_original.replace('${PRODUCT_NAME}', long_title)

	installer_plist = plist_original
	with open(plist_install, 'w+') as f:
		installer_plist = installer_plist.replace('${EXECUTABLENAME}', 'installer.bin')
		f.write(installer_plist)

	uninstaller_plist = plist_original
	with open(plist_uninstall, 'w+') as f:
		uninstaller_plist = uninstaller_plist.replace('${EXECUTABLENAME}', 'uninstaller.bin')
		f.write(uninstaller_plist)

	sys.stdout.write('Step 2, write mac specific vars in main template\n')
	sys.stdout.flush()
	template = open(tmplFinal, 'r').read()

	with open(tmplFinal, 'w+') as f:
		template = template.replace('${MACOS_INSTALLER_PLIST}', plist_install)
		template = template.replace('${MACOS_UNINSTALLER_PLIST}', plist_uninstall)
		f.write(template)

	sys.stdout.write('Step 3, create installer bin\n')
	sys.stdout.flush()
	cmd = ["%s/macos/packer.bin" % InstallerDir]
	cmd.append('-debug=1')
	cmd.append('-exe')
	cmd.append('-xml=%s' % unix_slashes(tmplFinal))
	cmd.append('-installer=%s' % "%s/macos/installer.bin" % InstallerDir)
	cmd.append('-filesdir=%s' % unix_slashes(InstallerDir))
	cmd.append('-outbin=%s/packed.bin' % tempfile.gettempdir())
	cmd.append('-dest=%s' % bin_path)
	cmd.append('-wmstr="bdbe6b7e-b69c-4ad8-b3d9-646bbeb5c3e1"')
	cmd.append('-wmval="580c154c-9043-493a-b436-f15ad8772763"')

	sys.stdout.write("[%s]\n" % ", ".join(cmd))
	sys.stdout.flush()
	if not self.mode_test:
		if subprocess.call(cmd) != 0:
			sys.stderr.write('Failed macos installer creation\n')
			sys.stderr.flush()
			sys.exit(1)

	st = os.stat(bin_path)
	os.chmod(bin_path, st.st_mode | stat.S_IEXEC)

	sys.stdout.write('Step 4, create app folder structure\n')
	sys.stdout.flush()
	app_dir = os.path.join(root_tmp, '%s.app' % target_name)
	os.mkdir(app_dir)
	os.mkdir(os.path.join(app_dir, 'Contents'))
	os.mkdir(os.path.join(app_dir, 'Contents', 'MacOS'))
	os.mkdir(os.path.join(app_dir, 'Contents', 'Resources'))

	shutil.copyfile('%s/macos/osx_installer/PkgInfo' % InstallerDir, os.path.join(app_dir, 'Contents', 'PkgInfo'))
	shutil.copyfile('%s/macos/osx_installer/mac.icns' % InstallerDir, os.path.join(app_dir, 'Contents', 'Resources', 'mac.icns'))

	installer_path_app = os.path.join(app_dir, 'Contents', 'MacOS', '%s.bin' % target_name)
	shutil.copyfile(bin_path, installer_path_app)

	st = os.stat(installer_path_app)
	os.chmod(installer_path_app, st.st_mode | stat.S_IEXEC)

	plist_tmpl = plist_original
	with open(os.path.join(app_dir, 'Contents', 'Info.plist'), 'w+') as f:
		plist_tmpl = plist_tmpl.replace('${EXECUTABLENAME}', '%s.bin' % target_name)
		f.write(plist_tmpl)

	sys.stdout.write('Step 5, create dmg file in %s\n' % root_tmp)
	sys.stdout.flush()
	os.chdir(root_tmp)
	dmg_file = '%s.dmg' % target_name
	# Add some megabytes for the package additional files (icons, plist, etc)
	dmg_target_size = str(os.path.getsize(installer_path_app) + 8 * 1024 * 1024)

	# should be executed in the order listed, grouped in dict for convenience
	commands = {
		'create_dmg':  ['hdiutil', 'create', '-size', dmg_target_size, '-layout', 'NONE', dmg_file],
		'mount_dmg':   ['hdid', '-nomount', dmg_file],
		'fs_dmg':      ['newfs_hfs', '-v', '%s' % short_title, None], # None = mount_dmg drive
		'eject_dmg':   ['hdiutil', 'eject', None], # None = mount_dmg drive
		'path_dmg':    ['hdid', dmg_file],
		'copy_app':    ['cp', '-r', '%s.app' % target_name, None], # None = vpath
		'eject_final': ['hdiutil', 'eject', None], # none = mout_dmg drie
	}

	sys.stdout.write("[%s]\n" % ", ".join(commands['create_dmg']))
	sys.stdout.flush()
	if _get_cmd_output_ex(commands['create_dmg'])['code'] != 0:
		sys.stderr.write('[%s] failed\n' % ', '.join(commands['create_dmg']))
		sys.stderr.flush()
		sys.exit(1)

	sys.stdout.write("[%s]\n" % ", ".join(commands['mount_dmg']))
	sys.stdout.flush()
	mount_res = _get_cmd_output_ex(commands['mount_dmg'])
	if mount_res['code'] != 0:
		sys.stderr.write('[%s] failed\n' % ', '.join(commands['mount_dmg']))
		sys.stderr.flush()
		sys.exit(1)

	commands['fs_dmg'][-1] = mount_res['output']
	commands['eject_dmg'][-1] = mount_res['output']
	commands['eject_final'][-1] = mount_res['output']

	sys.stdout.write("[%s]\n" % ", ".join(commands['fs_dmg']))
	sys.stdout.flush()
	if _get_cmd_output_ex(commands['fs_dmg'])['code'] != 0:
		sys.stderr.write('[%s] failed\n' % ', '.join(commands['fs_dmg']))
		sys.stderr.flush()
		sys.exit(1)

	sys.stdout.write("[%s]\n" % ", ".join(commands['eject_dmg']))
	sys.stdout.flush()
	if _get_cmd_output_ex(commands['eject_dmg'])['code'] != 0:
		sys.stderr.write('[%s] failed' % ', '.join(commands['eject_dmg']))
		sys.stderr.flush()
		sys.exit(1)

	sys.stdout.write("[%s]\n" % ", ".join(commands['path_dmg']))
	sys.stdout.flush()
	path_dmg_res = _get_cmd_output_ex(commands['path_dmg'])
	if path_dmg_res['code'] != 0:
		sys.stderr.write('[%s] failed' % ', '.join(commands['path_dmg']))
		sys.stderr.flush()
		sys.exit(1)

	disk, vpath = re.match(r'^([^\s]+)\s+(.+)$', path_dmg_res['output'], re.I | re.S).groups()
	commands['copy_app'][-1] = vpath

	sys.stdout.write("[%s]\n" % ", ".join(commands['copy_app']))
	sys.stdout.flush()
	if _get_cmd_output_ex(commands['copy_app'])['code'] != 0:
		sys.stderr.write('[%s] failed' % ', '.join(commands['copy_app']))
		sys.stderr.flush()
		sys.exit(1)

	sys.stdout.write("[%s]\n" % ", ".join(commands['eject_final']))
	sys.stdout.flush()
	if _get_cmd_output_ex(commands['eject_final'])['code'] != 0:
		sys.stderr.write('[%s] failed' % ', '.join(commands['eject_final']))
		sys.stderr.flush()
		sys.exit(1)

	sys.stdout.write('WD %s\n' % root_tmp)
	sys.stdout.flush()
	shutil.move(os.path.join(root_tmp, dmg_file), installer_path)


def generateWindowsInstaller(self, InstallerDir, tmplFinal, installer_path):
	packer = ["%s/windows/packer.exe" % InstallerDir]
	packer.append('-debug=1')
	packer.append('-exe')
	packer.append('-xml=%s' % unix_slashes(tmplFinal))
	packer.append('-filesdir=%s' % unix_slashes(InstallerDir))
	packer.append('-dest=%s' % installer_path)
	packer.append('-installer=%s' % "%s/windows/installer/installer.exe" % InstallerDir)
	packer.append('-outbin=%s' % "%s/out.bin" % tempfile.gettempdir())
	packer.append('-wmstr="ad6347ff-db11-47a5-9324-3d7bca5a94ac"')
	packer.append('-wmval="7d263cec-e754-456b-8d5c-1ffecdd796d7"')

	print(" ".join(packer))
	if not self.mode_test:
		if subprocess.call(packer) != 0:
			print('Failed with windows installer creation')
			sys.exit(1)


def generateLinuxInstaller(self, InstallerDir, tmplFinal, installer_path):
	packer = ["%s/linux/packer.bin" % InstallerDir]
	packer.append('-exe')
	packer.append('-debug=1')
	packer.append('-xml=%s' % unix_slashes(tmplFinal))
	packer.append('-filesdir=%s' % unix_slashes(InstallerDir))
	packer.append('-dest=%s' % "%s/console.bin" % tempfile.gettempdir())
	packer.append('-installer=%s' % "%s/linux/installer/console/installer.bin" % InstallerDir)
	packer.append('-outbin=%s' % "%s/lnx_intermediate.ibin" % tempfile.gettempdir())
	packer.append('-wmstr="bdbe6b7e-b69c-4ad8-b3d9-646bbeb5c3e1"')
	packer.append('-wmval="580c154c-9043-493a-b436-f15ad8772763"')

	print(" ".join(packer))
	if not self.mode_test:
		if subprocess.call(packer) != 0:
			print('Failed linux ibin creation')
			sys.exit(1)

	tmpl = open("%s/linux/launcher_wrapper.xml" % InstallerDir, 'r').read()
	wrapper_xml = "%s/launcher_wrapper.xml" % tempfile.gettempdir()

	with open(wrapper_xml, "w+") as f:
		tmpl = tmpl.replace("($IBIN_FILE)",        "%s/lnx_intermediate.ibin" % tempfile.gettempdir())
		tmpl = tmpl.replace("($INSTALLER_BIN)",    "installer.bin")
		tmpl = tmpl.replace("($UNINSTALLER_BIN)",  "uninstaller.bin")
		f.write(tmpl)

	cmd = ["%s/linux/packer.bin" % InstallerDir]

	cmd.append('-debug=1')
	cmd.append('-exe')
	cmd.append('-xml=%s' % wrapper_xml)
	cmd.append('-installer=%s' % "%s/linux/installer/launcher.bin" % InstallerDir)
	cmd.append('-filesdir=%s' % "%s/linux/installer" % InstallerDir)
	cmd.append('-outbin=%s' % "%s/packed.bin" % tempfile.gettempdir())
	cmd.append('-dest=%s' % installer_path)
	cmd.append('-wmstr="bdbe6b7e-b69c-4ad8-b3d9-646bbeb5c3e1"')
	cmd.append('-wmval="580c154c-9043-493a-b436-f15ad8772763"')

	print(" ".join(cmd))
	if not self.mode_test:
		if subprocess.call(cmd) != 0:
			print('Failed linux installer creation')
			sys.exit(1)


def GenCGRInstaller(self, installer_path, InstallerDir="H:/devel/vrayblender/cgr_installer"):
	sys.stdout.write("Generating CGR installer:\n")
	sys.stdout.write("  %s\n" % installer_path)

	# Collect installer files
	#
	removeJunk   = set()
	installerFiles = []

	installerFiles.append('\t\t\t<FN Dest="[INSTALL_ROOT]">%s/postinstall.py</FN>' % InstallerDir)

	empty_installer_files = [
		os.path.join(InstallerDir, 'assets/backup.bin'),
		os.path.join(InstallerDir, 'assets/install.log'),
	]

	for dirpath, dirnames, filenames in os.walk(self.dir_install_path):
		if dirpath.startswith('.svn') or dirpath.endswith('__pycache__'):
			continue

		rel_dirpath = os.path.normpath(dirpath).replace(os.path.normpath(self.dir_install_path), "")

		for f in os.listdir(dirpath):
			# skip weird cmake file
			if f == 'a.out':
				continue

			f_path = os.path.join(dirpath, f)
			if os.path.isdir(f_path):
				continue

			relInstDir  = unix_slashes(rel_dirpath)
			relInstDir  = relInstDir if relInstDir != '.' else ''

			absFilePath = unix_slashes(f_path)

			removeJunk.add('\t\t\t<Files Dest="[INSTALL_ROOT]%s" DeleteDirs="1">*.pyc</Files>' % (relInstDir))
			removeJunk.add('\t\t\t<Files Dest="[INSTALL_ROOT]%s" DeleteDirs="1">__pycache__</Files>' % (relInstDir))

			if not os.path.exists(absFilePath):
				stderr_log("os.walk(%s) [%s] does not exists" % (self.dir_install_path, absFilePath))
				continue
			st = os.stat(absFilePath)
			if st.st_size == 0:
				empty_installer_files.append(absFilePath)

			if st.st_mode & stat.S_IEXEC:
				installerFiles.append('\t\t\t<FN Executable="1" Dest="[INSTALL_ROOT]%s">%s</FN>' % (relInstDir, absFilePath))
			else:
				installerFiles.append('\t\t\t<FN Dest="[INSTALL_ROOT]%s">%s</FN>' % (relInstDir, absFilePath))

	appsdk_root = ''
	appsdkFile = ''
	host_os = get_host_os()

	# bin file generated from postinstall.py
	if host_os != WIN:
		removeJunk.add('\t\t\t<Files Dest="[INSTALL_ROOT]" DeleteDirs="1">blender.bin</Files>')

	# add the zmq server
	cg_root = os.path.normpath(os.path.join(get_default_install_path(), 'V-Ray', 'VRayZmqServer'))
	os_type = get_host_os()
	os_dir = "darwin" if os_type == MAC else os_type
	appsdk = os.path.join(os.environ['CGR_APPSDK_PATH'], 'bin')
	appsdkFile = ''

	if host_os == WIN:
		appsdkFile = 'VRaySDKLibrary.dll'
	elif host_os == LNX:
		appsdkFile = 'libVRaySDKLibrary.so'
	else:
		appsdkFile = "libVRaySDKLibrary.dylib"

	temp_appsdk = appsdk
	# copy appsdk so we can make modifications freely
	temp_appsdk = os.path.join(tempfile.gettempdir(), 'appsdk')
	if os.path.exists(temp_appsdk):
		remove_directory(temp_appsdk)
	shutil.copytree(appsdk, temp_appsdk)

	prepare_appsdk(temp_appsdk)

	appsdk_root = os.path.normpath(os.path.join(cg_root, 'appsdk'))

	# add the appsdk files
	for dirpath, dirnames, filenames in os.walk(temp_appsdk):
		rel_path = os.path.relpath(dirpath, temp_appsdk)
		dest_path = os.path.join(appsdk_root, rel_path)
		dest_path = dest_path if dest_path != '.' else ''
		for file_name in filenames:
			source_path = os.path.join(dirpath, file_name)

			st = os.stat(source_path)
			if st.st_size == 0:
				empty_installer_files.append(source_path)

			if st.st_mode & stat.S_IEXEC:
				installerFiles.append('\t\t\t<FN Executable="1" Dest="%s">%s</FN>\n' % (dest_path, source_path))
			else:
				installerFiles.append('\t\t\t<FN Dest="%s">%s</FN>\n' % (dest_path, source_path))


	zmq_items = get_zmq_build_items(self, appsdkFile)
	for item in zmq_items:
		st = os.stat(item)
		if st.st_size == 0:
			empty_installer_files.append(item)
		installerFiles.append('\t\t\t<FN Executable="1" Dest="%s">%s</FN>\n' % (cg_root, item))

	tmplFinal = "%s/installer.xml" % tempfile.gettempdir()
	if os.path.exists(tmplFinal):
		remove_file(tmplFinal)
	replace_file = '%s/%s/replace_file%s' % (InstallerDir, get_host_os(), '.exe' if get_host_os() == WIN else '')

	gen_tmpl = [replace_file]
	gen_tmpl.append('-inputfile="%s"' % ("%s/cgr_template.xml" % InstallerDir))
	gen_tmpl.append('-outputfile="%s"' % tmplFinal)
	gen_tmpl.append('-keyword="(%s$%s):true"' % ('\\' if get_host_os() != WIN else '', get_host_os().upper()))

	print(" ".join(gen_tmpl))
	if not self.mode_test:
		result = 0

		if get_host_os() == WIN:
			result = subprocess.call(" ".join(gen_tmpl))
		else:
			result = subprocess.call(gen_tmpl)

		if result != 0:
			print('replace_file failed')
			sys.exit(1)

	short_title = "Blender (With V-Ray Additions)"
	long_title = "Blender %s.%s (With V-Ray Additions)" % (self.versionArr[1], self.versionArr[2])

	# Write installer template
	tmpl = open(tmplFinal, 'r').read()
	with open(tmplFinal, 'w+') as f:
		# shortcuts
		if get_host_os() == WIN:
			tmpl = tmpl.replace("${SHORTCUTS_SECTION}", open("%s/shortcuts.xml" % InstallerDir, 'r').read())
		else:
			tmpl = tmpl.replace("${SHORTCUTS_SECTION}", '')

		# Default install dir
		tmpl = tmpl.replace("${PROGRAMFILES}",   get_default_install_path())

		tmpl = tmpl.replace("${APP_TITLE}",      short_title)
		tmpl = tmpl.replace("${APP_TITLE_FULL}", long_title)

		# Files
		tmpl = tmpl.replace("${FILE_LIST}", "\n".join(sorted(reversed(installerFiles))))
		tmpl = tmpl.replace("${RUNTIME_JUNK_LIST}", "\n".join(sorted(removeJunk)))
		tmpl = tmpl.replace("${INSTALL_XML_PATH}", tmplFinal)

		# Appsdk env var path
		if get_host_os() == WIN:
			# set it as env var from installer
			tmpl = tmpl.replace("${ZMQ_ENV_VARIABLE}", '<Replace VarName="VRAY_ZMQSERVER_APPSDK_PATH" IsPath="1">%s</Replace>'  % os.path.join(appsdk_root, appsdkFile))
			tmpl = tmpl.replace("${VRAY_ZMQSERVER_APPSDK_PATH}", '')
		else:
			# set it as argument for postinstall.py
			tmpl = tmpl.replace("${ZMQ_ENV_VARIABLE}", '')
			tmpl = tmpl.replace("${VRAY_ZMQSERVER_APPSDK_PATH}", '%s/%s'  % (appsdk_root, appsdkFile))

		# Versions
		tmpl = tmpl.replace("${VERSION_MAJOR}", self.versionArr[1])
		tmpl = tmpl.replace("${VERSION_MINOR}", self.versionArr[2])
		tmpl = tmpl.replace("${VERSION_SUB}",   self.versionArr[3])
		tmpl = tmpl.replace("${VERSION_CHAR}",  self.versionArr[4])

		tmpl = tmpl.replace("${VERSION_HASH}",       self.brev)
		tmpl = tmpl.replace("${VERSION_PATCH_HASH}", self.revision[:7])

		# Installer stuff
		tmpl = tmpl.replace("${INSTALLER_DATA_ROOT}", InstallerDir)


		# System stuff
		tmpl = tmpl.replace("${PLATFORM}", "x86_64")

		f.write(tmpl)

	total_lost_time = 0
	before_write = time.time()
	for fix_file_path in empty_installer_files:
		sys.stdout.write('File [%s] size == 0, will append one char\n' % fix_file_path)
		sys.stdout.flush()
		# TODO: unhack this when installer can handle 0 size files
		with open(fix_file_path, 'a') as file_fix:
			file_fix.write(' ')

	sys.stdout.write('Total time spent handling non empty files: %f seconds\n' % (time.time() - before_write))
	sys.stdout.flush()

	packer = []
	# Run installer generator
	if get_host_os() == WIN:
		generateWindowsInstaller(self, InstallerDir, tmplFinal, installer_path)
	elif get_host_os() == LNX:
		generateLinuxInstaller(self, InstallerDir, tmplFinal, installer_path)
	elif get_host_os() == MAC:
		generateMacInstaller(self, InstallerDir, tmplFinal, installer_path, short_title, long_title)

