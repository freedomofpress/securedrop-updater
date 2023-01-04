"""
General purpose migration steps
"""

import os
import shutil
import sys
import tempfile


class MigrationStep:
    def validate(self):
        return True

    def snapshot(self, directory):
        pass

    def run(self):
        pass

    def revert(self, directory):
        pass

    def cleanup(self):
        pass

    def __repr__(self):
        return f"<{self.__class__.__name__}: {self.__dict__}>"

    def __str__(self):
        return self.__repr__()


class PathMigrationStep(MigrationStep):
    def __init__(self, path, check_exists=None):
        self.path = path
        self.check_exists = check_exists

    def validate(self):
        if self.check_exists is not None:
            exists = os.path.exists(self.path)
            return exists == self.check_exists
        return True

    def snapshot(self, tmpdir):
        if self.check_exists is not None and self.check():
            shutil.copytree(self.path, tmpdir)

    def run(self):
        pass

    def revert(self, tmpdir):
        if self.check_exists is not None and self.check():
            basename = os.path.basename(self.path)
            shutil.move(f"{tmpdir}/{basename}", self.path)


class Remove(PathMigrationStep):
    def run(self):
        shutil.rmtree(self.file_path)


class Move(PathMigrationStep):
    def __init__(self, path, target, check_exists=None):
        super().__init__(path, check_exists)
        self.target = target

    def run(self):
        shutil.move(self.path, self.target)

    def revert(self, tmpdir):
        if os.path.exists(self.target):
            shutil.rmtree(self.target)
        super().revert(tmpdir)


class Symlink(PathMigrationStep):
    def __init__(self, path, target, check_exists=None):
        super().__init__(path, check_exists)
        self.target = target

    def run(self):
        os.symlink(self.path, self.target)


def _revert_steps(steps, failed_index, tmpdir):
    for step in steps[:failed_index]:
        step.revert(tmpdir)


def _clean_exit(tmpdir, rc):
    shutil.rmtree(tmpdir)
    sys.exit(rc)


def _validate(steps, tmpdir):
    # Before attempting to run anything, ensure that the required state is met
    for step in steps:
        if not step.validate():
            print(f"Failed during validation: {step}", file=sys.stderr)
            _clean_exit(tmpdir, 1)


def _snapshot(steps, tmpdir):
    for i, step in enumerate(steps):
        try:
            step.snapshot(tmpdir)
        except Exception as error:
            print(f"{error}", file=sys.stderr)
            _revert_steps(steps, i, tmpdir)
            print(f"Failed during snapshotting step {i}: {step}", file=sys.stderr)
            _clean_exit(tmpdir, 1)


def _run(steps, tmpdir):
    for i, step in enumerate(steps):
        try:
            step.run()
        except Exception as error:
            print(f"{error}: Reverting preceding steps", file=sys.stderr)
            _revert_steps(steps, i, tmpdir)
            print(f"Failed during running migration step {i}: {step}", file=sys.stderr)
            _clean_exit(tmpdir, 1)


def _cleanup(steps):
    for step in steps:
        # Having run migrations without
        try:
            step.cleanup()
        except Exception:
            pass


def migrate(steps):
    tmpdir = tempfile.mkdtemp()
    _validate(steps, tmpdir)
    _snapshot(steps, tmpdir)
    _run(steps, tmpdir)
    _cleanup(steps)
    _clean_exit(tmpdir, 0)
