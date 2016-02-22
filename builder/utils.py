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
import tempfile

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


def get_default_install_path():
	if get_host_os == WIN:
		return "C:/Program Files/Chaos Group/"
	elif get_host_os == MAC:
		return "/Applications/ChaosGroup/"
	else:
		return "/usr/ChaosGroup/"


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


def _get_cmd_output_ex(cmd, workDir=None):
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
			'hash'     : "-%s" % self.revision[:7],
		})

	return "{project}{version}{nCommits}{bhash}{hash}{arch}{branch}".format(**params)


def GetPackageName(self, ext=None):
	def _get_host_package_type():
		if get_host_os() == WIN:
			return "exe"
		elif get_host_os() == MAC:
			return 'dmg'
		else:
			return "bin"

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


def unix_slashes(path):
	return os.path.normpath(path.replace("\\", "/"))


def generateMacInstaller(self, InstallerDir, tmplFinal, installer_path, short_title, long_title):
	root_tmp = tempfile.mkdtemp()
	target_name = os.path.basename(installer_path).replace('.dmg', '')
	bin_path = installer_path.replac('.dmg', '.bin')

	print('Macos installer tmp wd %s' % root_tmp)

	print('Step 1, create uninstaller/installer plist files')
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

	print('Step 2, write mac specific vars in main template')
	template = open(tmplFinal, 'r').read()

	with open(tmplFinal, 'w+') as f:
		template = template.replace('${MACOS_INSTALLER_PLIST}', plist_install)
		template = template.replace('${MACOS_UNINSTALLER_PLIST}', plist_uninstall)
		f.write(template)

	print('Step 3, create installer bin')
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

	print(" ".join(cmd))
	if not self.mode_test:
		if subprocess.call(cmd) != 0:
			print('Failed macos installer creation')
			sys.exit(1)

	print('Step 4, create app folder structure')
	app_dir = os.path.join(root_tmp, '%s.app' % target_name)
	os.mkdir(app_dir)
	os.mkdir(os.path.join(app_dir, 'Contents'))
	os.mkdir(os.path.join(app_dir, 'Contents', 'MacOS'))
	os.mkdir(os.path.join(app_dir, 'Contents', 'Resources'))

	shutil.copyfile('%s/macos/osx_installer/PkgInfo' % InstallerDir, os.path.join(app_dir, 'Contents', 'PkgInfo'))
	shutil.copyfile('%s/macos/osx_installer/mac.icns' % InstallerDir, os.path.join(app_dir, 'Contents', 'Resources', 'mac.icns'))

	installer_path_app = os.path.join(app_dir, 'Contents', 'MacOS', '%s.bin' % target_name)
	shutil.move(bin_path, installer_path_app)

	# shutil.copyfile('%s/macos/osx_installer/Info.plist.in' % InstallerDir, os.path.join(app_dir, 'Contents', 'Info.plist'))
	plist_tmpl = plist_original
	with open(os.path.join(app_dir, 'Contents', 'Info.plist'), 'w+') as f:
		plist_tmpl = plist_tmpl.replace('${EXECUTABLENAME}', '%s.bin' % target_name)
		f.write(plist_tmpl)

	print('Step 5, create dmg file in %s' % root_tmp)
	os.chdir(root_tmp)
	dmg_file = '%s.dmg' % target_name
	# Add some megabytes for the package additional files (icons, plist, etc)
	dmg_target_size = str(os.path.getsize(installer_path_app) + 8 * 1024 * 1024)

	# should be executed in the order listed, grouped in dict for convenience
	commands = {
		'create_dmg':  ['hdiutil', 'create', '-size', dmg_target_size, '-layout', 'NONE', dmg_file],
		'mount_dmg':   ['hdid', '-nomount', dmg_file],
		'fs_dmg':      ['newfs_hfs', '-v', '"%s"' % short_title, None], # None = mount_dmg drive
		'eject_dmg':   ['hdiutil', 'eject', None], # None = mount_dmg drive
		'path_dmg':    ['hdid', dmg_file],
		'copy_app':    ['cp', '-r', '%s.app' % target_name, None], # None = vpath
		'eject_final': ['hdiutil', 'eject', None], # none = mout_dmg drie
	}

	print(commands['create_dmg'])
	if _get_cmd_output_ex(commands['create_dmg'])['code'] != 0:
		print('"%s" failed' % ' '.join(commands['create_dmg']))
		sys.exit(1)

	print(commands['mount_dmg'])
	mount_res = _get_cmd_output_ex(commands['mount_dmg'])
	if mount_res['code'] != 0:
		print('"%s" failed' % ' '.join(commands['mount_dmg']))
		sys.exit(1)

	commands['fs_dmg'][-1] = mount_res['output']
	commands['eject_dmg'][-1] = mount_res['output']
	commands['eject_final'][-1] = mount_res['output']

	print(commands['fs_dmg'])
	if _get_cmd_output_ex(commands['fs_dmg'])['code'] != 0:
		print('"%s" failed' % ' '.join(commands['fs_dmg']))
		sys.exit(1)

	print(commands['eject_dmg'])
	if _get_cmd_output_ex(commands['eject_dmg'])['code'] != 0:
		print('"%s" failed' % ' '.join(commands['eject_dmg']))
		sys.exit(1)

	print(commands['path_dmg'])
	path_dmg_res = _get_cmd_output_ex(commands['path_dmg'])
	if path_dmg_res['code'] != 0:
		print('"%s" failed' % ' '.join(commands['path_dmg']))
		sys.exit(1)

	disk, vpath = re.match(r'^([^\s]+)\s+(.+)$', path_dmg_res['output'], re.I | re.S).groups()
	commands['copy_app'][-1] = vpath

	print(commands['copy_app'])
	if _get_cmd_output_ex(commands['copy_app'])['code'] != 0:
		print('"%s" failed' % ' '.join(commands['copy_app']))
		sys.exit(1)

	print(commands['eject_final'])
	if _get_cmd_output_ex(commands['eject_final'])['code'] != 0:
		print('"%s" failed' % ' '.join(commands['eject_final']))
		sys.exit(1)

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
			installerFiles.append('\t\t\t<FN Dest="[INSTALL_ROOT]%s">%s</FN>' % (relInstDir, absFilePath))

	appsdk_root = ''
	appsdkFile = ''

	# add the zmq server if enabled
	if self.teamcity_zmq_server_hash != '' and self.teamcity_project_type == 'vb35':
		cg_root = os.path.join(get_default_install_path(), 'V-Ray', 'VRayZmqServer')
		zmq_name = ''
		appsdk = os.path.join(os.environ['CGR_APPSDK_PATH'], os.environ['CGR_APPSDK_VERSION'], get_host_os(), 'bin');
		appsdkFile = ''

		if get_host_os() == WIN:
			zmq_name = "VRayZmqServer.exe"
			appsdkFile = 'VRaySDKLibrary.dll'
		elif get_host_os() == LNX:
			zmq_name = "VRayZmqServer"
			appsdkFile = 'libVRaySDKLibrary.so'

		appsdk_root = os.path.join(cg_root, 'appsdk')

		# add the appsdk files
		for dirpath, dirnames, filenames in os.walk(appsdk):
			rel_path = os.path.relpath(dirpath, appsdk)
			dest_path = os.path.join(appsdk_root, rel_path)
			dest_path = dest_path if dest_path != '.' else ''
			for file_name in filenames:
				source_path = os.path.join(dirpath, file_name)
				installerFiles.append('\t\t\t<FN Dest="%s">%s</FN>\n' % (dest_path, source_path))

		zmq_build_path = ''
		if get_host_os() == WIN:
			zmq_build_path = "H:/install/vrayserverzmq/%s/V-Ray/VRayZmqServer/VRayZmqServer.exe" % self.teamcity_zmq_server_hash
		elif get_host_os() == LNX:
			zmq_build_path = "/home/teamcity/install/vrayserverzmq/%s/V-Ray/VRayZmqServer/VRayZmqServer" % self.teamcity_zmq_server_hash

		installerFiles.append('\t\t\t<FN Executable="1" Dest="%s">%s</FN>\n' % (cg_root, zmq_build_path))

	tmplFinal = "%s/installer.xml" % tempfile.gettempdir()
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
		if self.teamcity_zmq_server_hash != '' and self.teamcity_project_type == 'vb35':
			tmpl = tmpl.replace("${ZMQ_ENV_VARIABLE}", '<Replace VarName="VRAY_ZMQSERVER_APPSDK_PATH" IsPath="1">%s/%s</Replace>'  % (appsdk_root, appsdkFile))

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

	packer = []
	# Run installer generator
	if get_host_os() == WIN:
		generateWindowsInstaller(self, InstallerDir, tmplFinal, installer_path)
	elif get_host_os() == LNX:
		generateLinuxInstaller(self, InstallerDir, tmplFinal, installer_path)
	elif get_host_os() == MAC:
		generateMacInstaller(self, InstallerDir, tmplFinal, installer_path, short_title, long_title)

