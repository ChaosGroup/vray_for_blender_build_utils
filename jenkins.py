#
# V-Ray For Blender jenkins Build Wrapper
#
# http://chaosgroup.com
#
# Author: Andrei Izrantcev
# E-Mail: andrei.izrantcev@chaosgroup.com
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

import os
import sys
import subprocess

from builder import utils

def setup_msvc_2013(cgrepo):
    env = {
        'INCLUDE' : [
            "{CGR_SDK}/msvs2013/PlatformSDK/Include/shared",
            "{CGR_SDK}/msvs2013/PlatformSDK/Include/um",
            "{CGR_SDK}/msvs2013/PlatformSDK/Include/winrt",
            "{CGR_SDK}/msvs2013/PlatformSDK/Include/ucrt",
            "{CGR_SDK}/msvs2013/include",
            "{CGR_SDK}/msvs2013/atlmfc/include",
        ],

        'LIB' : [
            "{CGR_SDK}/msvs2013/PlatformSDK/Lib/winv6.3/um/x64",
            "{CGR_SDK}/msvs2013/PlatformSDK/Lib/ucrt/x64",
            "{CGR_SDK}/msvs2013/atlmfc/lib/amd64",
            "{CGR_SDK}/msvs2013/lib/amd64",
        ],

        'PATH' : [
                "{CGR_SDK}/msvs2013/bin/amd64",
                "{CGR_SDK}/msvs2013/bin",
                "{CGR_SDK}/msvs2013/PlatformSDK/bin/x64",
            ] + os.environ['PATH'].split(';')
        ,
    }
    os.environ['__MS_VC_INSTALL_PATH'] = "{CGR_SDK}/msvs2013"
    for var in env:
        os.environ[var] = ";".join(env[var]).format(CGR_SDK=cgrepo)


def main(args):
    if sys.platform == 'win32':
        setup_msvc_2013(args.jenkins_win_sdk_path)

    working_dir = os.path.join(args.jenkins_perm_path, 'blender-dependencies')
    if not os.path.exists(working_dir):
        os.makedirs(working_dir)

    branch = 'dev/vray_for_blender/%s' % args.jenkins_project_type
    # just for test
    args.jenkins_appsdk_version = '20160510'

    appsdk_path = os.path.join(working_dir, 'vray-appsdk')
    appsdk_check = os.path.join(appsdk_path, args.jenkins_appsdk_version, 'windows')
    if args.jenkins_project_type == 'vb35' and not os.path.exists(appsdk_check):
        os.makedirs(appsdk_check)
        ftpScriptFilepath = os.path.join(working_dir, "appsdk-download.txt")
        sys.stdout.write("Writing ftp command in %s" % ftpScriptFilepath)
        with open(ftpScriptFilepath, 'w') as f:
            f.write('option batch abort\n')
            f.write('option confirm off\n')
            f.write('open ftp://%s:%s@nightlies.chaosgroup.com -rawsettings ProxyMethod=2 ProxyHost=10.0.0.1 ProxyPort=1080\n' % (
                os.environ['JENKINS_USER'],
                os.environ['JENKINS_PASS'],
            ))
            f.write('option transfer binary\n')
            f.write('get /vrayappsdk/20160510/appsdk-win-qt-nightly-1.09.00-vray33501-20160510.7z %s/appsdk.7z\n' % appsdk_path)
            f.write('exit\n')
            f.write('\n')

        cmd = ['winscp']
        cmd.append('/passive')
        cmd.append('/script="%s"' % ftpScriptFilepath)
        os.system(' '.join(cmd))
        os.chdir(appsdk_check)
        os.system('7z x appsdk.7z')

    if args.jenkins_project_type == 'vb35':
        # add qt to path
        os.environ['PATH'] = os.path.join(args.jenkins_win_sdk_path, 'qt', '4.8.4') + ';' + os.environ['PATH'];
        sys.stdout.write('CGR_APPSDK_PATH [%s], CGR_APPSDK_VERSION [%s]' % (appsdk_path, args.jenkins_appsdk_version))
        os.environ['CGR_BUILD_TYPE'] = args.jenkins_build_type
        os.environ['CGR_APPSDK_PATH'] = appsdk_path
        os.environ['CGR_APPSDK_VERSION'] = args.jenkins_appsdk_version

    if args.jenkins_project_type:
        blender_modules = [
            "release/scripts/addons_contrib",
            "source/tools",
            "release/scripts/addons",
        ]

        if args.jenkins_project_type == 'vb35':
            blender_modules.append('intern/vray_for_blender_rt/extern/vray-zmq-wrapper')

        pwd = os.getcwd()
        os.chdir(working_dir)

        utils.get_repo('https://github.com/bdancer/blender-for-vray', branch=branch, submodules=blender_modules, target_dir=pwd, target_name='blender')
        utils.get_repo('https://github.com/ChaosGroup/blender-for-vray-libs', target_dir=pwd)

        if args.jenkins_project_type == 'vb35':
            utils.get_repo('https://github.com/bdancer/vrayserverzmq', target_dir=pwd, submodules=['extern/vray-zmq-wrapper'])

        os.chdir(pwd)


    python_exe = sys.executable

    sys.stdout.write('jenkins args:\n%s\n' % str(args))
    sys.stdout.flush()

    os.environ['http_proxy'] = '10.0.0.1:1234'
    os.environ['https_proxy'] = '10.0.0.1:1234'
    os.environ['ftp_proxy'] = '10.0.0.1:1234'
    os.environ['socks_proxy'] = '10.0.0.1:1080'

    os.environ['http_proxy'] = 'http://10.0.0.1:1234/'
    os.environ['https_proxy'] = 'https://10.0.0.1:1234/'

    cmd = [python_exe]
    cmd.append("vb25-patch/build.py")
    cmd.append("--jenkins")
    cmd.append("--teamcity_project_type=%s" % args.jenkins_project_type)

    cmd.append('--github-src-branch=%s' % branch)
    cmd.append('--teamcity_zmq_server_hash=%s' % utils.get_git_head_hash(os.path.join(os.getcwd(), 'vrayserverzmq')))

    cmd.append('--jenkins_win_sdk_path=%s' % args.jenkins_win_sdk_path)
    os.environ['JENKINS_WIN_SDK_PATH'] = args.jenkins_win_sdk_path
    cmd.append('--jenkins_output=%s' % args.jenkins_output)

    if args.clean:
        cmd.append('--build_clean')

    cmd.append('--with_ge')
    cmd.append('--with_player')
    cmd.append('--with_collada')
    cmd.append('--vc_2013')
    cmd.append('--build_mode=release')
    cmd.append('--build_type=%s' % args.jenkins_build_type)
    cmd.append('--use_package')
    cmd.append('--use_installer=CGR')
    cmd.append('--dir_cgr_installer=%s' % os.path.join(os.getcwd(), 'blender-for-vray-libs', 'cgr_installer'))

    if args.jenkins_with_static_libc:
        cmd.append('--jenkins_with_static_libc')

    cmd.append('--with_cycles')
    cmd.append('--uppatch=off')
    cmd.append('--upblender=off')

    cmd.append('--dir_install=%s' % os.path.join(args.jenkins_output, 'install', 'vray_for_blender'))
    cmd.append('--dir_release=%s' % os.path.join(args.jenkins_output, 'release', 'vray_for_blender'))

    if args.upload:
        cmd.append('--use_package_upload=ftp')
        cmd.append('--use_proxy=http://10.0.0.1:1234')

    sys.stdout.write('Calling builder:\n%s\n' % '\n\t'.join(cmd))
    sys.stdout.flush()

    return subprocess.call(cmd, cwd=os.getcwd())


if __name__ == '__main__':
    import argparse
    import sys

    parser = argparse.ArgumentParser(usage="python3 build.py [options]")

    parser.add_argument('--upload',
        default=False,
        help="Upload build"
    )

    parser.add_argument('--clean',
        default=False,
        help="Clean build directory"
    )

    parser.add_argument('--jenkins_output',
        default = ""
    )

    parser.add_argument('--jenkins_win_sdk_path',
        default = ""
    )

    parser.add_argument('--jenkins_appsdk_version',
        default = ""
    )

    parser.add_argument('--jenkins_perm_path',
        default = ""
    )

    parser.add_argument('--jenkins_project_type',
        choices=['vb30', 'vb35'],
        default = 'vb30',
    )

    parser.add_argument('--jenkins_with_static_libc',
        action = 'store_true',
    )

    parser.add_argument('--jenkins_build_type',
        choices=['debug', 'release'],
        default = 'release',
    )

    parser.add_argument('--jenkins_init_repos',
        action = 'store_true',
    )

    args = parser.parse_args()

    sys.exit(main(args))
