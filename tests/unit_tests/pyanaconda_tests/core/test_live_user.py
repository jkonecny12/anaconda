# -*- coding: utf-8 -*-
#
# Copyright (C) 2023  Red Hat, Inc.
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

import pytest

from unittest.mock import Mock
from pyanaconda.core import live_user
from pyanaconda.core.live_user import get_live_user, User


### FIXTURES ###

@pytest.fixture
def mocked_system_conf(monkeypatch):
    mocked_conf = Mock()
    mocked_system = Mock()
    mocked_conf.system = mocked_system

    monkeypatch.setattr(live_user, "conf", mocked_conf)

    return mocked_system


@pytest.fixture
def prepare_mocked_live_user(mocked_system_conf, monkeypatch):
    mocked_system_conf.provides_liveuser = True
    monkeypatch.setenv("PKEXEC_UID", "1024")


@pytest.fixture
def mocked_getpwuid(monkeypatch):
    m_getpwuid = Mock()
    monkeypatch.setattr(live_user, "getpwuid", m_getpwuid)

    return m_getpwuid


### TESTS ###


def test_get_live_user_not_on_live(mocked_system_conf, mocked_getpwuid):
    """Test get_live_user function not on live environment"""
    # not live = early exit
    mocked_system_conf.provides_liveuser = False
    assert get_live_user() is None
    mocked_getpwuid.assert_not_called()


def test_get_live_user_on_live(prepare_mocked_live_user, mocked_getpwuid):
    """Test get_live_user function"""
    # live and has user
    mocked_getpwuid.return_value = Mock(pw_uid=1024, pw_dir='/home/liveuser', pw_name='liveuser')
    assert get_live_user() == User(name="liveuser",
                                   uid=1024,
                                   env_prune=("GDK_BACKEND",),
                                   env_add={
                                       "XDG_RUNTIME_DIR": "/run/user/1024",
                                       "USER": "liveuser",
                                       "HOME": "/home/liveuser",
                                   })
    mocked_getpwuid.assert_called_once_with(1024)


def test_get_live_user_missing_PKEXEC_UID(prepare_mocked_live_user, mocked_getpwuid, monkeypatch):
    """Test get_live_user function not running in pkexec environment"""
    monkeypatch.delenv("PKEXEC_UID")
    assert get_live_user() is None


def test_get_live_user_broken_getpwuid_call(prepare_mocked_live_user, mocked_getpwuid):
    """Test get_live_user function with missing user"""
    # supposedly live but missing user
    mocked_getpwuid.side_effect = KeyError
    assert get_live_user() is None
    mocked_getpwuid.assert_called_once_with(1024)
