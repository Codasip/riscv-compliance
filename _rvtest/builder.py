# Copyright (c) 2018, Codasip Ltd.
# See LICENSE file for license details.

import os
import re
from subprocess import run
import time

from _rvtest.utils import info, error, warning, fatal


class Repository():
    """Simple git repository wrapper.
    
    Repository URL consists of three components, which are neccessary when creating a new instance.
    ``https://<remote>/<owner>/<repository>``, e.g. ``https://github.com/riscv/riscv-compliance` `
    """
    def __init__(self, remote, owner, repository, user='git', dir=None):
        """Constructor.
        
        :param remote: Address of the remote server.
        :param owner: Repository owner. 
        :param repository: Repository name.
        :param dir: Path to git repository root. Defaults to repository name.
        :type remote: str
        :type owner: str
        :type repository: str
        :type dir: str
        :ivar url: Absolute URL to GIT repository.
        :vartype: str
        """
        self.remote = remote
        self.owner = owner
        self.user = user
        self.repository = repository[:-4] if repository.endswith('.git') else repository
        self.url = "https://{}/{}/{}.git".format(self.remote, self.owner, self.repository)
        self._branch = None
        
        # Automatically set dir
        if dir is None:
            dir = os.path.join(os.getcwd(), self.repository)
        self.dir = os.path.abspath(dir)
        
    def clone(self, branch=None):
        """Clone repository.
        
        :param branch: Branch to clone. If ``None``, then default branch is cloned.
        :type branch: str or None
        
        .. note::
            
            Clones recursively.
        
        """
        args = ['git', 'clone', '--recursive', self.url, self.dir]
        if branch:
            args += ['-b', branch]
        info("Cloning {} to {}{}".format(self.url, self.dir, ' (branch %s)'%branch if branch else ''))
        run(args)
        
        if branch:
            self._branch = branch
    
    def pull(self):
        """Pull repository."""
        args = ['git', 'pull']
        info("Pulling {}".format(self.dir))
        run(args, cwd=self.dir)
    
    def checkout(self, branch):
        """Checkout a certain branch.
        
        :param branch: Branch to checkout.
        :type branch: str
        """
        if branch == self.branch:
            info("Repository {} is already on branch {}".format(self.repository, branch))
            return
        args = ['git', 'checkout', branch]
        # just to be sure, do fetch
        self._fetch()
        info("Switching branch from {} to {} in {}".format(self.branch, branch, self.dir))
        run(args, cwd=self.dir)
        self._branch = branch

    def synchronize(self, branch=None, submodules=False):
        """Synchronize repository with remote server.
        
        If repository has not been initialized yet, then
        it is recursively cloned from remote server. Otherwise
        pull or checkout operation is performed.
        
        :param branch: Branch to synchronize local repository with.
            If ``None`` then actual (if already cloned) or default (if not cloned)
            branch will be used.
        :type branch: str or ``None``
        
        """
        # Already cloned, just pull
        if self.is_initialized():
            info("Repository already cloned, trying to checkout or pull")
            if branch and branch != self.branch:
                self.checkout(branch)
            else:
                self.pull()
        else:
            self.clone(branch)
        if submodules:
            self._get_submodules()
        
    
    def _get_submodules(self):
        """Clone submodules."""
        info("Checking-out submodules")
        args = ['git', 'submodule', 'update', 'init', '--recursive']
        run(args, cwd=self.dir)
        
    def _fetch(self):
        """Standard git fetch of the repository."""
        args = ['git', 'fetch']
        info("Fetching %s..."%self.repository)
        run(args, cwd=self.dir)
    
    def is_initialized(self):
        """Detect if repository is cloned"""
        return (os.path.isdir(os.path.join(self.dir, '.git')) and
                len(os.listdir(self.dir)) > 1)
    
    @property
    def branch(self):
        """Return current branch."""
        # Not cloned yet
        if not self.is_initialized():
            return None
        # Use cached branch
        if self._branch:
            return self._branch
        args = ['git', 'rev-parse', '--abbrev-ref', 'HEAD']
        out = run(args, cwd=self.dir).stdout
        branch = None
        if out:
            branch = out.rstrip('\n').split('/')[-1]
        
        # Repository might be cloned using fetch and checkout.
        # In that case branch contains 'HEAD' -> use another way
        # to detect branch.
        if not branch or branch == 'HEAD':
            args = ['git', 'log', '-n', '1', '--pretty=%d', 'HEAD']
            out = run(args, cwd=self.dir).stdout
            match = re.search('origin/([\w\-\._]+)', out.strip())
            if match:
                branch = match.group(1)
        self._branch = branch
        return branch

    @property
    def current_commit(self):
        """Return current commit hash of repository."""
        if not self.is_initialized():
            return None
        cmd = ['git', 'rev-parse', 'HEAD']
        commit = run(cmd, cwd=self.dir).stdout.rstrip()
        return commit
        

    @property
    def id(self):
        """Build repository ID.
        
        :return: Unique repository ID with owner, repository
            and branch. These parts are separated by colon.
        :rtype: str
        """
        lst = [self.owner, self.repository]
        if self.branch:
            lst.append(self.branch)
        
        return ':'.join(lst)
    
    @classmethod
    def from_url(cls, url, dir=None):
        """Initialize repository from git url."""
        # Cut user and server
        pattern = r'https://(?P<remote>.+)/(?P<owner>.+)/(?P<repo>.+)(.git)?'
        
        m = re.search(pattern, url)

        return cls(m.group('remote'), m.group('owner'), m.group('repo'), dir=dir)
    
    @classmethod
    def from_dir(cls, dir):
        """Initialize repository from cloned directory.
        
        :param dir: Directory containing GIT repository.
        :type dir: str
        :return: Initialized Repository object.
        :rtype: :py:class:`Repository`
        """
        # Get remote url
        cmd = ['git', 'config', '--get', 'remote.origin.url']
        url = run(cmd,cwd=dir).stdout.rstrip()
        # dir might be subdirectory of an actual git repository
        cmd = ['git', 'rev-parse', '--show-toplevel']
        dir = run(cmd, cwd=dir).stdout.rstrip()
        return cls.from_url(url, dir)
    
    def __repr__(self):
        return "<Repository {}, dir={}, state={}>".format(self.id, self.dir, 
                                                          ("initialized" if self.is_initialized() 
                                                           else "uninitialized"))

class RVToolchainBuilder():
    """Builder for Risc-V Toolchain and reference model
    
    :todo: Fails after repositories checkout.
    """
    
    URL = 'https://github.com/riscv/riscv-tools.git'
    WAIT_BEFORE_BUILD = 8
    
    def __init__(self, work_dir=None):
        if work_dir is None:
            work_dir = os.path.join(os.getcwd(), 'toolchain')

        self.work_dir = os.path.abspath(work_dir)
        self.repository = Repository.from_url(self.URL, self.work_dir)
        self._script = os.path.join(self.repository.dir, 'build.sh') 
    
    def build(self, output):
        if output is None:
            output = os.getenv('RISCV', self.work_dir)
        output = os.path.abspath(output)
        
        info(f'RISC-V toolchain will be built to {output}')
        info(f'Please make sure you have installed all prerequisities. Prerequisities can be found at {self.URL[:-4]}/blob/master/README.md')
        time.sleep(self.WAIT_BEFORE_BUILD)
        
        if not os.path.exists(self.work_dir):
            os.makedirs(self.work_dir)
        # Checkout repositories recursively
        self.repository.synchronize(submodules=True)
        
        env = os.environ.copy()
        env.setdefault('RISCV', output)
        return run(['sh', self._script], cwd=self.work_dir, env=env).returncode
        