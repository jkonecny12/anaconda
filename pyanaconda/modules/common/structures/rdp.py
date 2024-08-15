#
# DBus structure for module ui module RDP data.
#
# Copyright (C) 2024 Red Hat, Inc.
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
from dasbus.structure import DBusData
from dasbus.typing import *  # pylint: disable=wildcard-import

from pyanaconda.modules.common.structures.secret import SecretData

__all__ = ["RdpData"]


class RdpData(DBusData):
    """Module Rdp runtime data"""

    def __init__(self):
        self._enabled = False
        self._host = ""
        self._port = -1
        self._username = ""
        self._password = SecretData()

    @property
    def enabled(self) -> Bool:
        """Whether RDP is enabled.

        :return: True if enabled, False otherwise.
        """
        return self._enabled

    @enabled.setter
    def enabled(self, value: Bool):
        self._enabled = value

    @property
    def host(self) -> Str:
        """The RDP host address.

        This could be an IP address or a hostname where the RDP server is running.

        :return: a host address.
        """
        return self._host

    @host.setter
    def host(self, value: Str):
        self._host = value

    @property
    def port(self) -> Int:
        """The RDP port number.

        This is the port on which the RDP server is listening.

        Value -1 means it is not set.

        :return: a port number as a int.
        """
        return self._port

    @port.setter
    def port(self, value: Int):
        self._port = value

    @property
    def username(self) -> Str:
        """Name of the user.

        This is username used by the RDP client.

        :return: username as string
        """
        return self._username

    @username.setter
    def username(self, value: Str):
        self._username = value

    @property
    def password(self) -> SecretData:
        """The RDP password.

        This is the password required to connect to the RDP server.

        :return: a password.
        """
        return self._password

    @password.setter
    def password(self, value: SecretData):
        self._password = value
