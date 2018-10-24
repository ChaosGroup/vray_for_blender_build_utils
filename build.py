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


import argparse
import os
import sys
import multiprocessing

import builder as build_system

cwd     = os.getcwd()
host_os = build_system.utils.get_host_os()


parser = argparse.ArgumentParser(usage="python3 build.py [options]")


gr_paths = parser.add_argument_group(title="Paths")
gr_paths.add_argument('--dir_blender_libs',
	default = '',
	help    = "Directory for blender lib deps",
	metavar = 'FILE'
)
gr_paths.add_argument('--dir_source',
	default = cwd,
	help    = "Root directory",
	metavar = 'FILE'
)
gr_paths.add_argument('--dir_build',
	help    = "Build directory.",
	default = os.path.join(cwd, "build"),
	metavar = 'FILE'
)
gr_paths.add_argument('--dir_install',
	help    = "Installation directory.",
	default = os.path.join(cwd, "install"),
	metavar = 'FILE'
)
gr_paths.add_argument('--dir_release',
	help    = "Directory for installer / archive",
	default = os.path.join(cwd, "release"),
	metavar = 'FILE'
)
gr_paths.add_argument('--dir_cgr_installer',
	help    = "Directory for installer / archive",
	default = "",
	metavar = 'FILE'
)

gr_compilation = parser.add_argument_group(title="Compilation")
gr_compilation.add_argument('--build_type',
	default = 'release',
	choices = {'release', 'debug'},
	help    = "Build type"
)
gr_compilation.add_argument('--build_clean',
	dest    = 'build_clean',
	default = False,
	action  = 'store_true',
	help    = "Clear build directory before building"
)
gr_compilation.add_argument('--build_export_only',
	dest    = 'export_only',
	action  = 'store_true',
	default = False,
	help    = "Don't compile"
)
gr_compilation.add_argument('--build_jobs',
	default = multiprocessing.cpu_count(),
	help    = "Number of build threads"
)
gr_compilation.add_argument('--vc_from_env',
	dest    = "use_env_msvc",
	action  = 'store_true',
	default = False,
	help    = "Use compiler from the environment (Windows only)"
)
gr_compilation.add_argument('--vc_2013',
	dest    = "vc2013",
	action  = 'store_true',
	default = False,
	help    = "Use VC 2013 libraries (Windows only)"
)
gr_compilation.add_argument('--gcc',
	dest    = "gcc",
	default = "",
	help    = "GCC"
)
gr_compilation.add_argument('--gxx',
	dest    = "gxx",
	default = "",
	help    = "G++"
)

gr_release = parser.add_argument_group(title="Release")
gr_release.add_argument('--use_package',
	action  = 'store_true',
	default = False,
	help    = "Create archive (Linux / OS X) or installer (Windows, NSIS required)"
)
gr_release.add_argument('--use_installer',
	default =  'NSIS',
	choices = {'NSIS', 'CGR'},
	help    = "Installer system"
)
gr_release.add_argument('--use_archive',
	default = False,
	help    = "Generate archive"
)
gr_release.add_argument('--add-branch-name',
	action  = 'store_true',
	dest    = "add_branch_name",
	default = False,
	help    = "Append branch name to the installer / archive name"
)


gr_comp = parser.add_argument_group(title="Blender Components")
gr_comp.add_argument('--with_collada',
	action='store_true',
	help="Build with OpenCollada support"
)
gr_comp.add_argument('--with_player',
	action='store_true',
	help="Build with Blender Player"
)
gr_comp.add_argument('--with_ge',
	action='store_true',
	help="Build with Blender Game Engine"
)
gr_comp.add_argument('--with_cycles',
	action='store_true',
	help="Build with Cycles"
)
gr_comp.add_argument('--with_osl',
	action='store_true',
	help="Build Cycles with OSL support"
)
gr_comp.add_argument('--with_tracker',
	action='store_true',
	help="Build with motion tracker support"
)


gr_src = parser.add_argument_group(title="Sources")
gr_src.add_argument('--upblender',
	default = 'on',
	choices = {'on', 'off'},
	help    = "Update Blender sources"
)
gr_src.add_argument('--uppatch',
	default = 'on',
	choices = {'on', 'off'},
	help="Update patch sources"
)
gr_src.add_argument(
	'--github-src-branch',
	dest    = "use_github_branch",
	default = "dev/vray_for_blender/vb35",
	help    = "Use sources from specific branch"
)
gr_src.add_argument(
	'--github-exp-branch',
	dest    = "use_exp_branch",
	default = "master",
	help    = "Use exporter from specific branch"
)
gr_src.add_argument(
	'--use_blender_hash',
	dest    = "use_blender_hash",
	default = "",
	help    = "Use specific revision"
)


gr_deps = parser.add_argument_group(title="Build Dependencies (Linux Only)")
gr_deps.add_argument('--build_deps',
	action  = 'store_true',
	default = False,
	help    = "Build dependencies using BF build script")
gr_deps.add_argument('--install_deps',
	action  = 'store_true',
	default = False,
	help="Install dependencies (Gentoo, OpenSuse, Fedora, Ubuntu)"
)


gr_script = parser.add_argument_group(title="Build Script Debug")
gr_script.add_argument('--debug',  action='store_true', dest='mode_debug', default=False, help="Script debug output.")
gr_script.add_argument('--test',   action='store_true', dest='mode_test',  default=False, help="Test mode.")


# Special options used only by me
#
parser.add_argument('--mode_developer',
	default = False,
	help    = argparse.SUPPRESS # Don't clone exporter and update vb25-patch basically
)
parser.add_argument('--dev_static_libs',
	action  = 'store_true',
	default = False,
	help    = argparse.SUPPRESS # Use my precompiled static dependency libraries
)
parser.add_argument('--build_mode',
	default = 'nightly',
	choices = {'release', 'nightly'},
	help    = argparse.SUPPRESS # Option for CGR installer
)
parser.add_argument('--target_version_suffix',
	default = '35',
	help    = 'Version suffix to append to filename' # Option for CGR installer
)
parser.add_argument('--use_package_upload',
	default = 'off',
	choices = {'off', 'ftp', 'http'},
	help    = argparse.SUPPRESS
)
parser.add_argument('--use_proxy',
	default = "",
	help    = argparse.SUPPRESS
)

parser.add_argument('--branch_hash',
	default = "",
	help    = argparse.SUPPRESS
)
parser.add_argument('--zmq_server_hash',
	default = "",
	help    = argparse.SUPPRESS
)
parser.add_argument('--with_static_libc',
	action = 'store_true',
	help    = argparse.SUPPRESS
)

# Jenkins
parser.add_argument('--jenkins',
	action  = 'store_true',
	help    = argparse.SUPPRESS
)
parser.add_argument('--jenkins_output',
	default = "",
	help    = argparse.SUPPRESS
)
parser.add_argument('--jenkins_minimal_build',
	action='store_true',
	default=False,
	required=False,
	help    = argparse.SUPPRESS
)

args = parser.parse_args()


if args.build_deps:
	build_system.linux.DepsBuild(args)

elif args.install_deps:
	build_system.linux.DepsInstall(args)

else:
	builder = build_system.Builder(vars(args))
	builder.build()
