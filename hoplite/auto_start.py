from argparse import ArgumentParser
import sys
import os
import shutil
import platform


# TODO: Modify this to support custom port numbers
def main(args=sys.argv):
    '''
    Calls a batch file to start hoplite-server on boot.
    '''
    parser = ArgumentParser(
        description='Installs the hoplite-server in the startup directory.')
    parser.add_argument('-d', '--disable', action='store_true',
                        help='Disables auto start on boot.',
                        dest='disable')
    if args == sys.argv:
        args = args[1:]
    args = parser.parse_args(args)
    args = vars(args)
    working_dir = os.path.dirname(os.path.realpath(__file__))
    batch = os.path.join(working_dir, 'hoplite.bat')
    dest = ''
    if platform.release() == 'XP':
        dest = os.path.join(os.environ['allusersprofile'], 'Start Menu',
                            'Programs', 'Startup', 'hoplite.bat')
    else:
        dest = os.path.join(os.environ['allusersprofile'], 'Microsoft',
                            'Windows', 'Start Menu', 'Programs', 'Startup',
                            'hoplite.bat')
    if args['disable']:
        os.remove(dest)
        print('Hoplite auto start successfully disabled.')
    else:
        shutil.copyfile(batch, dest)
        print('Hoplite successfully configured to start on boot.')
