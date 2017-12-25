import logging
import os
import subprocess

log = logging.getLogger('git_cloner')
log.setLevel(logging.DEBUG)

class RepoCloner:

    @staticmethod
    def clone(slug, repos_folder, url):
        try:
            repos_folder = os.path.abspath(repos_folder)
            log.info(msg='Cloning repo {0}'.format(slug))
            cmd = 'git clone {0} {1} --recursive'.format(url, slug)
            process = subprocess.Popen(cmd.split(), cwd=repos_folder, stdout=subprocess.PIPE)
            output, _ = process.communicate()
            log.info(output.decode("utf-8").strip())
        except Exception as e:
            log.error('Error cloning repo {0}: {1}'.format(slug, e))

    @staticmethod
    def pull(dest):
        try:
            dest = os.path.abspath(dest)
            cmd = 'git pull origin master'
            process = subprocess.Popen(cmd.split(), cwd=dest, stdout=subprocess.PIPE)
            output, _ = process.communicate()
            log.info(output.decode("utf-8").strip())
        except Exception as e:
            log.error('Error pulling git repo at {0}'.format(e))
