#
# Copyright (C) 2022  Red Hat, Inc.
#
# This copyrighted material is made available to anyone wishing to use,
# modify, copy, or redistribute it subject to the terms and conditions of
# the GNU General Public License v.2, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY expressed or implied, including the implied warranties of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General
# Public License for more details.  You should have received a copy of the
# GNU General Public License along with this program; if not, write to the
# Free Software Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301, USA.  Any Red Hat trademarks that are incorporated in the
# source code or documentation are not subject to the GNU General Public
# License and may only be used or replicated with the express permission of
# Red Hat, Inc.
#
import os
import tempfile
import unittest
from unittest.mock import patch

from pyanaconda.core.path import make_directories, join_paths, touch
from pyanaconda.modules.payloads.payload.dnf.repositories import generate_driver_disk_repositories


class DNFDriverDiskRepositoriesTestCase(unittest.TestCase):
    """Test the generate_driver_disk_repositories function."""

    @patch("pyanaconda.modules.payloads.payload.dnf.repositories.conf")
    def test_no_repository(self, conf_mock):
        """Test with no driver disk repositories."""
        conf_mock.system.can_use_driver_disks = True
        with tempfile.TemporaryDirectory() as d:
            assert generate_driver_disk_repositories(d) == []

    @patch("pyanaconda.modules.payloads.payload.dnf.repositories.conf")
    def test_empty_repository(self, conf_mock):
        """Test with empty driver disk repositories."""
        conf_mock.system.can_use_driver_disks = True
        with tempfile.TemporaryDirectory() as d:
            make_directories(join_paths(d, "DD-1"))
            assert generate_driver_disk_repositories(d) == []

    @patch("pyanaconda.modules.payloads.payload.dnf.repositories.conf")
    def test_repository_without_metadata(self, conf_mock):
        """Test with one driver disk repository without metadata."""
        conf_mock.system.can_use_driver_disks = True
        with tempfile.TemporaryDirectory() as d:
            make_directories(join_paths(d, "DD-1"))
            touch(join_paths(d, "DD-1", "x.rpm"))
            assert not os.path.exists(join_paths(d, "DD-1", "repodata"))

            (r, *rs) = generate_driver_disk_repositories(d)

            assert rs == []
            assert r.name == "DD-1"
            assert r.url == "file://{}/DD-1".format(d)
            assert os.path.exists(join_paths(d, "DD-1", "repodata"))

    @patch("pyanaconda.modules.payloads.payload.dnf.repositories.conf")
    def test_repository_with_metadata(self, conf_mock):
        """Test with one driver disk repository."""
        conf_mock.system.can_use_driver_disks = True
        with tempfile.TemporaryDirectory() as d:
            make_directories(join_paths(d, "DD-1"))
            make_directories(join_paths(d, "DD-1", "repodata"))
            touch(join_paths(d, "DD-1", "x.rpm"))

            (r, *rs) = generate_driver_disk_repositories(d)

            assert rs == []
            assert r.name == "DD-1"
            assert r.url == "file://{}/DD-1".format(d)

    @patch("pyanaconda.modules.payloads.payload.dnf.repositories.conf")
    def test_repositories(self, conf_mock):
        """Test with multiple driver disk repositories."""
        conf_mock.system.can_use_driver_disks = True
        with tempfile.TemporaryDirectory() as d:
            make_directories(join_paths(d, "DD-1"))
            touch(join_paths(d, "DD-1", "x.rpm"))

            make_directories(join_paths(d, "DD-2"))
            touch(join_paths(d, "DD-2", "y.rpm"))

            make_directories(join_paths(d, "DD-3"))
            touch(join_paths(d, "DD-3", "z.rpm"))

            (r1, r2, r3, *rs) = generate_driver_disk_repositories(d)

            assert rs == []
            assert r1.name == "DD-1"
            assert r1.url == "file://{}/DD-1".format(d)

            assert r2.name == "DD-2"
            assert r2.url == "file://{}/DD-2".format(d)

            assert r3.name == "DD-3"
            assert r3.url == "file://{}/DD-3".format(d)

    @patch("pyanaconda.modules.payloads.payload.dnf.repositories.conf")
    def test_disabled(self, conf_mock):
        """Test when disabled with one driver disk repository.

        This is a copy of test_repository_with_metadata but with the code disabled.
        """
        conf_mock.system.can_use_driver_disks = False
        with tempfile.TemporaryDirectory() as d:
            make_directories(join_paths(d, "DD-1"))
            make_directories(join_paths(d, "DD-1", "repodata"))
            touch(join_paths(d, "DD-1", "x.rpm"))

            assert generate_driver_disk_repositories(d) == []