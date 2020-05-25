import os
import subprocess
import shutil
import pwd
import grp
from os.path import join as j
from unittest import TestCase


class TestBase(TestCase):
    def __init__(self, *args, **kwargs):
        self.working_dir = os.path.realpath(__name__)
        self.calling_user = pwd.getpwuid(os.getuid())[0]
        self.calling_prim_group = grp.getgrgid(os.getgid())[0]
        super().__init__(*args, **kwargs)

    def fabricate(self, paths):
        for path in paths:
            path = j(self.working_dir, 'source', path)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, 'w') as f:
                f.write(path)
        return j(self.working_dir, 'source')

    def setUp(self):
        if os.path.exists(self.working_dir):
            self.tearDown()
        os.makedirs(self.working_dir, exist_ok=False)

    def tearDown(self):
        # Needs to force the rights because of locks etc.
        subprocess.check_call(["chmod", "700", "-R", self.working_dir])
        shutil.rmtree(self.working_dir)
