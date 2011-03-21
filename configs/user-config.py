#
# V-Ray/Blender
#

import sys

PLATFORM= sys.platform

WITH_BF_QUICKTIME = 'False'
WITH_BF_FMOD = 'False'
WITH_BF_ICONV = 'False'
WITH_BF_STATICOPENGL = 'False'
WITH_BF_VERSE = 'False'
WITH_BF_GAMEENGINE = 'False'
WITH_BF_PLAYER = 'False'
WITH_BF_COLLADA = 'False'

WITH_BF_INTERNATIONAL = 'True'
WITH_BF_JPEG = 'True'
WITH_BF_PNG = 'True'
WITH_BF_FFMPEG = 'True'
WITH_BF_OPENAL = 'True'
WITH_BF_SDL = 'True'
WITH_BF_BULLET = 'True'
WITH_BF_ZLIB = 'True'
WITH_BF_FTGL = 'True'
WITH_BF_RAYOPTIMIZATION = 'True'
WITH_BF_OPENEXR = 'True'

WITH_BUILDINFO = 'True'

BF_OPENAL_LIB = 'openal alut'
BF_TWEAK_MODE = 'false'
BF_PYTHON_VERSION = '3.2'
BF_NUMJOBS = 4

if PLATFORM == "win32":
	BF_INSTALLDIR = "C:\\vb25"
	BF_SPLIT_SRC = 'true'
	BF_BUILDDIR = "C:\\b"
else:
	SUFFIX =			"m"
	BF_PYTHON =			"/usr"
	BF_PYTHON_LIBPATH = "${BF_PYTHON}/lib"
	BF_PYTHON_INC =		"${BF_PYTHON}/include/python${BF_PYTHON_VERSION}" + SUFFIX
	BF_PYTHON_BINARY =	"${BF_PYTHON}/bin/python${BF_PYTHON_VERSION}"
	BF_PYTHON_LIB =		"python${BF_PYTHON_VERSION}" + SUFFIX

	BF_INSTALLDIR = "/opt/blender-2.5"
	BF_BUILDDIR = "/tmp/build-b25"

	CCFLAGS = ['-pipe','-fPIC','-funsigned-char','-fno-strict-aliasing']
	CPPFLAGS = ['-DXP_UNIX']
	CXXFLAGS = ['-pipe','-fPIC','-funsigned-char','-fno-strict-aliasing']
	REL_CFLAGS = ['-O2']
	REL_CCFLAGS = ['-O2']
	C_WARN = ['-Wno-char-subscripts', '-Wdeclaration-after-statement']
	CC_WARN = ['-Wall']
