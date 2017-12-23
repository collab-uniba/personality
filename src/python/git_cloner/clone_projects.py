import getopt
import logging
import os
import sys

from git import Repo

from gitutils.repo import RepoCloner
from loggingcfg import initialize_logger
from szzUtils import slugToFolderName


def start(argv):
    project_file = 'project-list.txt'
    destination_dir = './git_repos'
    symlink_dir = None

    try:
        if not argv:
            raise getopt.GetoptError('No arguments passed from the command line. See help instructions.')
        opts, args = getopt.getopt(argv, "hf:t:s:", ["from=", "to=", "symlink=", "help"])
        for opt, arg in opts:
            if opt in ("-h", "--help"):
                print('Usage:\n clone_projects.py -f|--from=<file> -t|--to=<dir> [-s|--symlink=<dir>]')
                sys.exit(0)
            elif opt in ("-f", "--from"):
                project_file = arg
                if not os.path.exists(project_file):
                    logger.error('%s does not exist.' % project_file)
            elif opt in ("-t", "--to"):
                destination_dir = os.path.abspath(arg)
                os.makedirs(destination_dir, exist_ok=True)
            elif opt in ("-s", "--symlink"):
                symlink_dir = os.path.abspath(arg)
                os.makedirs(symlink_dir, exist_ok=True)
            else:
                assert False, "unhandled option"
    except getopt.GetoptError as err:
        # print help information and exit:
        logger.error(err)  # will print something like "option -a not recognized"
        print('Usage:\n clone_projects.py -f|--from=<file> -t|--to=<dir> [-s|--symlink=<dir>]')
        sys.exit(1)

    logging.info("Starting project cloning.")
    with open(project_file, 'r') as projects:
        for slug in projects:
            slug = slug.strip()
            s2f = slugToFolderName(slug)
            dest = os.path.join(destination_dir, s2f)

            if os.path.exists(dest):
                logger.info(
                    'Project {0} already available locally in {1}, performing an update.'.format(slug, dest))
                try:
                    RepoCloner.pull(dest)
                    RepoCloner.update_submodules(dest)
                except:
                    logger.error("Unknown error updating git repo in folder %s" % dest)
            else:
                RepoCloner.clone(slug, destination_dir)
                logger.info('Project repository {0} cloned into {1}'.format(slug, s2f))
                RepoCloner.update_submodules(dest)
            if symlink_dir:
                try:
                    sym = os.path.join(symlink_dir, s2f)
                    os.symlink(dest, sym)
                except FileExistsError:
                    logger.debug('Symlink already existing.')
                    pass

    logging.info('Done.')


if __name__ == '__main__':
    logger = initialize_logger('git_cloner')
    start()
