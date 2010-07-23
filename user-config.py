#
# V-Ray/Blender
#

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
WITH_BUILDINFO = 'True'
WITH_BF_OPENEXR = 'True'

BF_OPENAL_LIB = 'openal alut'
BF_TWEAK_MODE = 'false'
BF_PYTHON_VERSION = '3.1'
BF_NUMJOBS = 4
BF_INSTALLDIR = "/opt/vb25"
BF_BUILDDIR = "/tmp/build-vb25"

CCFLAGS = ['-pipe','-fPIC','-funsigned-char','-fno-strict-aliasing']
CPPFLAGS = ['-DXP_UNIX']
CXXFLAGS = ['-pipe','-fPIC','-funsigned-char','-fno-strict-aliasing']
REL_CFLAGS = ['-O2']
REL_CCFLAGS = ['-O2']
C_WARN = ['-Wno-char-subscripts', '-Wdeclaration-after-statement']
CC_WARN = ['-Wall']
