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


import optparse
import os
import sys

import builder as build_system


host_os = build_system.utils.get_host_os()

parser = optparse.OptionParser(usage="python %prog [options]", version="2.0")

parser.add_option('', '--sourcedir',                         dest='sourcedir',                    help="Source directory.", metavar= 'FILE')
parser.add_option('', '--installdir',                        dest='installdir',                   help="Installation directory.", metavar= 'FILE')
parser.add_option('', '--builddir',                          dest='builddir',                     help="Build directory.", metavar= 'FILE')
parser.add_option('', '--releasedir',                        dest='releasedir',                   help="Directory for package (installer or archive).", metavar= 'FILE')
parser.add_option('', '--release',    action='store_true',   dest='release',      default=False,  help="Release build.")
parser.add_option('', '--package',    action='store_true',   dest='package',      default=False,  help="Create archive (Linux, Mac OS) or installer (Windows, NSIS required).")
parser.add_option('', '--upload',                            dest='upload',       default='off',  help="Upload build", type='choice', choices=('off', 'ftp', 'http'))
parser.add_option('', '--proxy',                             dest='proxy',        default="",     help="Upload using proxy")
parser.add_option('', '--export_only', action='store_true',  dest='export_only',  default=False,  help="Don't compile")

# Blender options
parser.add_option('', '--with_collada', action='store_true',  dest='collada',      default=False,  help="Add OpenCollada support.")
parser.add_option('', '--with_player',  action='store_true',  dest='player',       default=False,  help="Build Blender Player.")
parser.add_option('', '--with_game',    action='store_true',  dest='game',         default=False,  help="Build with Blender Game Engine.")
parser.add_option('', '--with_cycles',  action='store_true',  dest='with_cycles',  default=False,  help="Add Cycles.")
parser.add_option('', '--with_cuda',    action='store_true',  dest='with_cuda',    default=False,  help="Build Cycles with CUDA kernels.")
parser.add_option('', '--cuda_gpu',                           dest='cuda_gpu',     default="sm_21",help="CUDA GPU version.")
parser.add_option('', '--with_osl',     action='store_true',  dest='with_osl',     default=False,  help="Build Cycles with OSL support.")
parser.add_option('', '--with_tracker', action='store_true',  dest='with_tracker', default=False,  help="Add motion tracker support.")

# Updates
parser.add_option('', '--upblender',                          dest='upblender',   default='on',   help="Update Blender sources.", type= 'choice', choices=('on', 'off'))
parser.add_option('', '--uppatch',                            dest='uppatch',     default='on',   help="Update patch sources.",   type= 'choice', choices=('on', 'off'))

# Building options
parser.add_option('', '--exporter_cpp',action='store_true', dest='exporter_cpp',default=True,   help="Use new cpp exporter.")
parser.add_option('', '--debug_build', action='store_true', dest='debug',       default=False,  help="Debug build.")
parser.add_option('', '--rebuild',     action='store_true', dest='rebuild',     default=False,  help="Full rebuild.")
parser.add_option('', '--revision',                         dest='revision',    default="",     help="Checkout particular SVN revision.")
parser.add_option('', '--nopatches',   action='store_true', dest='nopatches',   default=False,  help="Don't apply V-Ray/Blender patches.")
parser.add_option('', '--nodatafiles', action='store_true', dest='nodatafiles', default=False,  help="Don't add splash screen.")
parser.add_option('', '--addextra',    action='store_true', dest='addextra',    default=False,  help="Apply \"extra\" patches.")
parser.add_option('', '--optimize',    action='store_true', dest='optimize',    default=False,  help="Use compiler optimizations.")
parser.add_option('', '--jobs',                             dest='jobs',        default=4,      help="Number of build threads.")
if host_os == build_system.utils.MAC:
	parser.add_option('', '--osx',                          dest='osx',         default="10.6", help="Mac OS X version.")
	parser.add_option('', '--osx_arch',                     dest='osx_arch',    default="x86_64", help="Mac OS X architecture.", type= 'choice', choices=('x86', 'x86_64'))
if host_os == build_system.utils.LNX:
	parser.add_option('', '--build_deps',     action='store_true', dest='build_deps',     default=False,  help="Build dependencies using BF build script.")
	parser.add_option('', '--use_build_deps', action='store_true', dest='use_build_deps', default=True,   help="Use builded dependencies.")
	parser.add_option('', '--install_deps',   action='store_true', dest='deps',           default=False,  help="Install dependencies (Gentoo, OpenSuse, Fedora, Ubuntu).")
	parser.add_option('', '--docs',           action='store_true', dest='docs',           default=False,  help="Build Python API documentation (python-sphinx required).")
	parser.add_option('', '--desktop',        action='store_true', dest='desktop',        default=False,  help="Generate .desktop file.")

# Script options
parser.add_option('', '--clean',     action='store_true', dest='build_clean', default=False, help="Clear build directory before building")
parser.add_option('', '--debug',     action='store_true', dest='mode_debug', default=False, help="Script debug output.")
parser.add_option('', '--test',      action='store_true', dest='mode_test',  default=False, help="Test mode.")
parser.add_option('', '--developer', action='store_true', dest='mode_devel', default=False, help=optparse.SUPPRESS_HELP) # Special mode used only by me =)

parser.add_option('', '--user_config', dest='user_user_config', default="", help="User defined user-config.py")

parser.add_option('', '--env',    action='store_true', dest="use_env_msvc", default=False, help="Use compiler from the environment")
parser.add_option('', '--vc2013', action='store_true', dest="vc2013",       default=False, help="Use VC 2013 libraries")

parser.add_option('', '--github-src-branch', dest="use_github_branch", default="dev/vray_for_blender/stable", help="Use sources from project's github branch")
parser.add_option('', '--github-exp-branch', dest="use_exp_branch",    default="master", help="Use exporter from specific branch")

parser.add_option('',
	'--add-branch-name',
	action='store_true',
	dest="add_branch_name",
	default=False,
	help="Add branch name to the installer name"
)

parser.add_option('', '--vb30',
	action  = 'store_true',
	dest    = "vb30",
	default = False,
	help    = "Build vb30"
)

parser.add_option('', '--use_blender_hash',
	dest    = "use_blender_hash",
	default = "",
	help    = "Use revision (like 772af36fc469e7666fc59d1d0b0e4dbcf52cfe2c)"
)

(options, args) = parser.parse_args()


params = {}

# Assuming current directory as source directory by default
params['dir_source']     = os.getcwd()
if options.sourcedir:
	params['dir_source'] = build_system.utils.path_slashify(options.sourcedir)

# Default build directory
if host_os == build_system.utils.WIN:
	# Its vital to use short path here like C:\b\
	params['dir_build'] = "C:\\b\\"
else:
	params['dir_build'] = "/tmp/builder/"

if options.builddir:
	params['dir_build'] = build_system.utils.path_slashify(options.builddir)

if options.installdir:
	params['dir_install'] = build_system.utils.path_slashify(options.installdir)

if options.releasedir:
	params['dir_release'] = build_system.utils.path_slashify(options.releasedir)

params['update_blender'] = True if options.upblender == 'on' else False
params['update_patch']   = True if options.uppatch == 'on' else False

params['generate_package'] = options.package

params['use_debug']  = options.debug

params['build_release']  = options.release
params['build_threads']  = int(options.jobs)

params['mode_debug']     = options.mode_debug
params['mode_developer'] = options.mode_devel
params['mode_test']      = options.mode_test

params['add_datafiles']  = not options.nodatafiles
params['add_extra']      = options.addextra

params['with_tracker']   = options.with_tracker
params['with_player']    = options.player
params['with_ge']        = options.game

params['exporter_cpp']   = options.exporter_cpp

params['build_clean'] = options.build_clean

if host_os == build_system.utils.LNX:
	params['generate_docs']  = options.docs
	params['install_deps']   = options.deps
	params['build_deps']     = options.build_deps
	params['use_build_deps'] = options.use_build_deps

if host_os == build_system.utils.MAC:
	params['build_arch'] = options.osx_arch

if params['build_release']:
	# Just for sure to disable debug for release build
	params['use_debug'] = False

	params['build_upload'] = options.upload
	params['use_proxy']    = options.proxy

# Just for sure to disable 'Developer' mode if OS is not Linux
if host_os != build_system.utils.LNX:
	params['mode_developer'] = False

if options.revision:
	params['checkout_revision'] = options.revision

params['with_cycles'] = options.with_cycles
params['with_cuda']   = options.with_cuda
params['cuda_gpu']    = options.cuda_gpu
params['with_osl']    = options.with_osl

params['use_env_msvc'] = options.use_env_msvc

if options.user_user_config:
	params['user_user_config'] = options.user_user_config

params['use_github_branch'] = options.use_github_branch
params['add_branch_name']   = options.add_branch_name
params['add_patches']       = False
params['add_extra']         = False

params['use_exp_branch'] = options.use_exp_branch

params['vb30']   = options.vb30
params['vc2013'] = options.vc2013
params['export_only'] = options.export_only
params['use_blender_hash'] = options.use_blender_hash

builder = build_system.Builder(params)
builder.build()
