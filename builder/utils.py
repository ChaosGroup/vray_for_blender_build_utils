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


import commands
import getpass
import os
import platform
import re
import socket
import sys


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
		arch = 'x86' if commands.getoutput('uname -p') == 'i386' else 'x86_64'
	
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


def path_join(*args):
	"""
	  Joins path components for sure that
	  Windows paths will contain double back-slashes
	"""
	path = None
	
	if get_host_os() == WIN:
		path = '\\\\'.join(args)
		path = path.replace('\\\\\\\\','\\\\')
		path = path.replace('\\\\\\','\\\\')
	else:
		path = os.path.join(*args)
	
	#return os.path.normpath(path)
	return path


def path_create(path):
	if not os.path.exists(path):
		sys.stdout.write("Directory (%s) doesn\'t exist! Trying to create...\n" % (path))
		os.makedirs(path)


def path_expand(path):
	"""
	  Expands some special chars to real values
	"""
	if(path[0:1] == '~'):
		path = my_path_join(os.environ["HOME"],path[2:])
	
	elif(path[0:1] != '/'):
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


def find_git_patch():
	env_paths = os.getenv('PATH').split(';')
	
	for path in env_paths:
		if path.find('Git') == -1 and path.find('cmd') == -1:
			continue
		
		full_path = path_join(path, "..", "bin", "patch.exe")
		full_path = os.path.normpath(full_path)
		
		sys.stdout.write("Using \"patch.exe\" from Git (%s)\n" % (full_path))

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


def find_patch():
	if get_host_os() == WIN:
		# Try to use patch.exe from Git installation
		patch_exe = find_git_patch()
		if patch_exe is not None:
			return '"%s"' % (patch_exe)
		
		# Try to find patch.exe in %PATH%
		if which("patch.exe") is not None:
			return "patch.exe"

		# Try to find patch in Git installation
		# without using environment variables
		git_common_paths = [
			path_join("C:", "Program Files", "Git", "bin", "patch.exe"),
			path_join("C:", "Program Files (x86)", "Git", "bin", "patch.exe"),
		]

		for path in git_common_paths:
			if os.path.exists(path):
				return '"%s"' % (path)
	
	else:
		if which("patch") is not None:
			return "patch"

	sys.stderr.write("Fatal error!\n")
	sys.stderr.write("Patch command not found!!\n")
	sys.exit(2)


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


def get_svn_revision(svn_root):
	try:
		entries= open(path_join(svn_root,'.svn','entries'), 'r').read()
	except IOError:
		pass
	else:
		if re.match('(\d+)', entries):
			rev_match = re.search('\d+\s+dir\s+(\d+)', entries)
			if rev_match:
				return rev_match.groups()[0]
	return REVISION


def get_blender_version(root_dir):
	BKE_blender_h_path = path_join(root_dir, "source", "blender", "blenkernel", "BKE_blender.h")

	if not os.path.exists(BKE_blender_h_path):
		return VERSION

	BKE_blender_h = open(BKE_blender_h_path,'r').readlines()

	for line in BKE_blender_h:
		if line.find("BLENDER_VERSION") != -1:
			line = line.replace('\t', ' ')

			version_number = line.split(' ')[-1].strip()
			version        = version_number[:1] + "." + version_number[1:]

			return version
	
	return VERSION


def get_linux_distribution():
	long_info  = platform.linux_distribution()
	short_info = platform.dist()
	
	info = {}
	info['long_name']  = long_info[0].strip()
	info['short_name'] = short_info[0].lower().replace(' ','_').strip()
	info['version']    = short_info[1].strip()

	# I'm a happy Calculate Linux user =)
	if info['long_name'].find('Calculate Linux') != -1:
		info['short_name'] = 'Calculate'

	return info


def python_get_suffix(path, version):
	for s in ('m', 'mu', 'd', 'dmu'):
		if os.path.exists("%s%s%s" % (path,version,s)):
			return s
	return ""
