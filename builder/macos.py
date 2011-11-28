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


import sys

from builder import utils
from builder import Builder


class MacBuilder(Builder):
	pass

# ofile.write("BF_QUIET    = 1\n")
# ofile.write("BF_BUILDDIR = \"/tmp/%s-build\"\n" % project)
# ofile.write("BF_NUMJOBS  = 2\n")

# ofile.write("MACOSX_ARCHITECTURE      = '%s'\n" % MAC_CPU)
# ofile.write("MAC_CUR_VER              = '%s'\n" % OSX)
# ofile.write("MAC_MIN_VERS             = '%s'\n" % OSX)
# ofile.write("MACOSX_DEPLOYMENT_TARGET = '%s'\n" % OSX)
# ofile.write("MACOSX_SDK               = '/Developer/SDKs/MacOSX%s.sdk'\n" % OSX)
# ofile.write("LCGDIR                   = '#../lib/darwin-9.x.universal'\n")
# ofile.write("LIBDIR                   = '#../lib/darwin-9.x.universal'\n")

# ofile.write("CC                       = 'gcc-4.2'\n")
# ofile.write("CXX                      = 'g++-4.2'\n")

# ofile.write("USE_SDK                  = True\n")
# ofile.write("WITH_GHOST_COCOA         = True\n")
# ofile.write("WITH_BF_QUICKTIME        = False\n")

# ofile.write("ARCH_FLAGS = ['%s']\n" % ('-m32' if ARCH == 'x86' else '-m64'))

# ofile.write("CFLAGS     = ['-pipe','-funsigned-char'] + ARCH_FLAGS\n")

# ofile.write("CPPFLAGS   = [] + ARCH_FLAGS\n")
# ofile.write("CCFLAGS    = ['-pipe','-funsigned-char'] + ARCH_FLAGS\n")
# ofile.write("CXXFLAGS   = ['-pipe','-funsigned-char'] + ARCH_FLAGS\n")

# ofile.write("SDK_FLAGS          = ['-isysroot', MACOSX_SDK, '-mmacosx-version-min='+MAC_MIN_VERS, '-arch', MACOSX_ARCHITECTURE]\n")
# ofile.write("PLATFORM_LINKFLAGS = ['-fexceptions','-framework','CoreServices','-framework','Foundation','-framework','IOKit','-framework','AppKit','-framework','Cocoa','-framework','Carbon','-framework','AudioUnit','-framework','AudioToolbox','-framework','CoreAudio','-framework','OpenAL']+ARCH_FLAGS\n")
# ofile.write("PLATFORM_LINKFLAGS = ['-mmacosx-version-min='+MAC_MIN_VERS, '-Wl', '-isysroot', MACOSX_SDK, '-arch', MACOSX_ARCHITECTURE] + PLATFORM_LINKFLAGS\n")
# ofile.write("CCFLAGS  = SDK_FLAGS + CCFLAGS\n")
# ofile.write("CXXFLAGS = SDK_FLAGS + CXXFLAGS\n")
# ofile.write("REL_CFLAGS  = ['-DNDEBUG', '-O2','-ftree-vectorize','-msse','-msse2','-msse3','-mfpmath=sse']\n")
# ofile.write("REL_CCFLAGS = ['-DNDEBUG', '-O2','-ftree-vectorize','-msse','-msse2','-msse3','-mfpmath=sse']\n")
# ofile.write("REL_CFLAGS  = REL_CFLAGS + ['-march=core2','-mssse3','-with-tune=core2','-enable-threads']\n")
# ofile.write("REL_CCFLAGS = REL_CCFLAGS + ['-march=core2','-mssse3','-with-tune=core2','-enable-threads']\n")