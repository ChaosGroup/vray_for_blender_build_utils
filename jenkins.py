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
import re
import sys
import glob
import time
import json
import platform
import subprocess

from builder import utils

def main(args):
    sys.stdout.write('jenkins args:\n%s\n' % str(args))
    sys.stdout.flush()

    gitRefs = {
        'blender': args.jenkins_blender_git_ref,
        'zmq': args.jenkins_zmq_branch,
        'libs': args.jenkins_libs_git_ref,
        'exporter': args.jenkins_exporter_git_ref,
    }

    if args.jenkins_predefined_config == 'vb40':
        gitRefs = {
            'blender': 'dev/vray_for_blender/vb40',
            'zmq': 'dev/vray_for_blender/vb40',
            'libs': 'dev/vray_for_blender/vb40',
            'exporter': 'dev/vray_for_blender/vb40',
        }
    elif args.jenkins_predefined_config == 'vb35':
        gitRefs = {
            'blender': 'dev/vray_for_blender/vb35',
            'zmq': 'master',
            'libs': 'master',
            'exporter': 'master',
        }

    utils.stdout_log('GIT refs:')
    utils.stdout_log(json.dumps(gitRefs, indent=4))

    # minimal build is only true if build_mode == 'default'
    minimal_build = False
    if args.jenkins_build_mode == 'default':
        minimal_build = args.jenkins_minimal_build  in ['1', 'yes', 'true']
        args.jenkins_build_mode = 'nightly'
        sys.stdout.write('\n\tjenkins_build_mode is set to "default", building "nightly" version and *not* uploading\n')
        sys.stdout.flush()

    dir_build = os.getcwd()
    os.environ['http_proxy'] = 'http://10.0.0.1:1234/'
    os.environ['https_proxy'] = 'https://10.0.0.1:1234/'
    os.environ['ftp_proxy'] = '10.0.0.1:1234'
    os.environ['socks_proxy'] = '10.0.0.1:1080'

    dir_source = os.path.join(args.jenkins_perm_path, 'blender-dependencies')
    if not os.path.exists(dir_source):
        os.makedirs(dir_source)
    else:
        # if job is interrupted while in git operation this file is left behind
        lock_file = os.path.join(dir_source, 'vrayserverzmq','.git','modules','extern','vray-zmq-wrapper','modules','extern','cppzmq','index.lock')
        if os.path.exists(lock_file):
            utils.remove_path(lock_file)

    ### CLONE REPOS
    blender_modules = [
        "release/scripts/addons_contrib",
        "source/tools",
        "release/scripts/addons",
        'intern/vray_for_blender_rt/extern/vray-zmq-wrapper',
        'release/datafiles/locale', # WITH_INTERNATIONAL
    ]

    os.chdir(dir_source)
    utils.get_repo('git@github.com:ChaosGroup/blender_with_vray_additions',
                   branch=gitRefs['blender'],
                   submodules=blender_modules,
                   target_name='blender')

    utils.get_repo('ssh://gitolite@mantis.chaosgroup.com:2047/vray_for_blender_libs',
                   branch=gitRefs['libs'],
                   target_name='blender-for-vray-libs')

    utils.get_repo('ssh://gitolite@mantis.chaosgroup.com:2047/vray_for_blender_server.git',
                   branch=gitRefs['zmq'],
                   submodules=['extern/vray-zmq-wrapper'],
                   target_name='vrayserverzmq')

    utils.get_repo('gitolite@gitolite.chaosgroup.com:bintools',
                   target_name='bintools')

    ### ADD NINJA TO PATH
    ninja_path = 'None'
    if sys.platform == 'win32':
        ninja_path = os.path.join(dir_source, 'blender-for-vray-libs', 'Windows')
    else:
        ninja_path = os.path.join(os.environ['CI_ROOT'], 'ninja', 'ninja')
    sys.stdout.write('Ninja path [%s]\n' % ninja_path)
    sys.stdout.flush()
    os.environ['PATH'] = ninja_path + os.pathsep + os.environ['PATH']

    os.chdir(dir_build)

    ### ADD APPSDK PATH
    bl_libs_os_dir_name = {
        utils.WIN: 'Windows',
        utils.LNX: 'Linux',
        utils.MAC: 'Darwin',
    }[utils.get_host_os()]
    appsdk_path = os.path.join(dir_source, 'blender-for-vray-libs', bl_libs_os_dir_name, 'appsdk')
    appsdk_version = '20170307'# re.match(r'.*?vray\d{5}-(\d{8})\.(?:tar\.xz|7z)*?', appsdk_remote_name).groups()[0]
    os.environ['CGR_APPSDK_PATH'] = appsdk_path
    python_exe = sys.executable


    cmd = [python_exe]
    cmd.append("vb25-patch/build.py")
    cmd.append("--jenkins")
    cmd.append('--dir_source=%s' % dir_source)
    cmd.append('--dir_build=%s' % dir_build)

    cmd.append('--github-src-branch=%s' % gitRefs['blender'])
    cmd.append('--zmq_server_hash=%s' % utils.get_git_head_hash(os.path.join(dir_source, 'vrayserverzmq')))

    cmd.append('--jenkins_output=%s' % args.jenkins_output)


    dir_blender_libs = os.path.join(dir_source, 'prebuilt-libs')
    if not os.path.exists(dir_blender_libs):
        sys.stdout.write('Missing prebuilt-libs path [%s], trying to create\n' % dir_blender_libs)
        sys.stdout.flush()
        os.makedirs(dir_blender_libs)
    cmd.append('--dir_blender_libs=%s' % dir_blender_libs)

    if gitRefs['exporter'] != 'master':
        cmd.append('--github-exp-branch=%s' % gitRefs['exporter'])

    cmd.append('--build_clean')
    cmd.append('--with_ge')
    cmd.append('--with_player')
    cmd.append('--with_collada')
    cmd.append('--with_cycles')
    cmd.append('--with_tracker')
    if utils.get_host_os() == utils.WIN:
        cmd.append('--vc_2013')

    if minimal_build:
        cmd.append('--jenkins_minimal_build')
    cmd.append('--build_mode=%s' % args.jenkins_build_mode)
    cmd.append('--build_type=%s' % args.jenkins_build_type)
    cmd.append('--use_package')
    cmd.append('--use_installer=CGR')
    cmd.append('--dir_cgr_installer=%s' % os.path.join(dir_source, 'blender-for-vray-libs', 'cgr_installer'))

    if args.jenkins_with_static_libc:
        cmd.append('--with_static_libc')

    cmd.append('--dev_static_libs')

    cmd.append('--upblender=off')
    cmd.append('--uppatch=off')

    cmd.append('--gcc=gcc')
    cmd.append('--gxx=g++')

    cmd.append('--dir_install=%s' % os.path.join(args.jenkins_output, 'install', 'vray_for_blender'))
    cmd.append('--dir_release=%s' % os.path.join(args.jenkins_output, 'release', 'vray_for_blender'))

    sys.stdout.write('Calling builder:\n%s\n' % '\n\t'.join(cmd))
    sys.stdout.flush()

    return subprocess.call(cmd, cwd=dir_build)


if __name__ == '__main__':
    import argparse
    import sys

    parser = argparse.ArgumentParser(usage="python3 jenkins.py [options]")

    parser.add_argument('--jenkins_output',
        default = "",
        required=True,
    )

    parser.add_argument('--jenkins_perm_path',
        default = "",
        required=True,
    )

    parser.add_argument('--jenkins_blender_git_ref',
        default = "dev/vray_for_blender/vb35",
        required=False,
    )

    parser.add_argument('--jenkins_exporter_git_ref',
        default = "master",
        required=False,
    )

    parser.add_argument('--jenkins_libs_git_ref',
        default = "master",
        required=False,
    )

    parser.add_argument('--jenkins_with_static_libc',
        action = 'store_true',
    )

    parser.add_argument('--jenkins_build_mode',
        choices=['nightly', 'release', 'default'],
        default='default',
    )

    parser.add_argument('--jenkins_zmq_branch',
        default='master'
    )

    parser.add_argument('--jenkins_predefined_config',
        default='vb35',
        choices=['vb35', 'vb40', 'custom'],
        required=False,
    )

    parser.add_argument('--jenkins_minimal_build',
        default='0',
        choices=['yes', 'no', '1', '0', 'true', 'false'],
        required=False,
    )

    parser.add_argument('--jenkins_build_type',
        choices=['debug', 'release'],
        default = 'release',
        required=True,
    )

    args = parser.parse_args()

    sys.exit(main(args))
