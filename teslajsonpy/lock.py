#  SPDX-License-Identifier: Apache-2.0
"""
Python Package for controlling Tesla API.

For more details about this api, please refer to the documentation at
https://github.com/zabuldon/teslajsonpy
"""
import time

from teslajsonpy.vehicle import VehicleDevice


class Lock(VehicleDevice):
    """Home-assistant lock class for Tesla vehicles.

    This is intended to be partially inherited by a Home-Assitant entity.
    """

    def __init__(self, data, controller):
        """Initialize the locks for the vehicle.

        Parameters
        ----------
        data : dict
            The base state for a Tesla vehicle.
            https://tesla-api.timdorr.com/vehicle/state/data
        controller : teslajsonpy.Controller
            The controller that controls updates to the Tesla API.

        Returns
        -------
        None

        """
        super().__init__(data, controller)
        self.__manual_update_time = 0
        self.__lock_state = False

        self.type = "door lock"
        self.hass_type = "lock"

        self.name = self._name()

        self.uniq_name = self._uniq_name()
        self.bin_type = 0x7

    async def async_update(self):
        """Update the lock state."""
        await super().async_update()
        last_update = self._controller.get_last_update_time(self._id)
        if last_update >= self.__manual_update_time:
            data = self._controller.get_state_params(self._id)
            self.__lock_state = data["locked"] if data else None

    async def lock(self):
        """Lock the doors."""
        if not self.__lock_state:
            data = await self._controller.command(
                self._id, "door_lock", wake_if_asleep=True
            )
            if data and data["response"]["result"]:
                self.__lock_state = True
            self.__manual_update_time = time.time()

    async def unlock(self):
        """Unlock the doors and extend handles where applicable."""
        if self.__lock_state:
            data = await self._controller.command(
                self._id, "door_unlock", wake_if_asleep=True
            )
            if data and data["response"]["result"]:
                self.__lock_state = False
            self.__manual_update_time = time.time()

    def is_locked(self):
        """Return whether doors are locked."""
        return self.__lock_state

    @staticmethod
    def has_battery():
        """Return whether the device has a battery."""
        return False


class ChargerLock(VehicleDevice):
    """Home-assistant lock class for the charger of Tesla vehicles.

    This is intended to be partially inherited by a Home-Assitant entity.
    """

    def __init__(self, data, controller):
        """Initialize the charger lock for the vehicle.

        Parameters
        ----------
        data : dict
            The base state for a Tesla vehicle.
            https://tesla-api.timdorr.com/vehicle/state/data
        controller : teslajsonpy.Controller
            The controller that controls updates to the Tesla API.

        Returns
        -------
        None

        """
        super().__init__(data, controller)
        self.__manual_update_time = 0
        self.__lock_state = False

        self.type = "charger door lock"
        self.hass_type = "lock"

        self.name = self._name()

        self.uniq_name = self._uniq_name()
        self.bin_type = 0x7

    async def async_update(self):
        """Update state of the charger lock."""
        await super().async_update()
        last_update = self._controller.get_last_update_time(self._id)
        if last_update >= self.__manual_update_time:
            data = self._controller.get_charging_params(self._id)
            self.__lock_state = (
                not (
                    (data["charge_port_door_open"])
                    and (data["charge_port_latch"] != "Engaged")
                )
                if data
                else None
            )

    async def lock(self):
        """Close the charger door."""
        if not self.__lock_state:
            data = await self._controller.command(
                self._id, "charge_port_door_close", wake_if_asleep=True
            )
            if data and data["response"]["result"]:
                self.__lock_state = True
            self.__manual_update_time = time.time()

    async def unlock(self):
        """Open the charger door."""
        if self.__lock_state:
            data = await self._controller.command(
                self._id, "charge_port_door_open", wake_if_asleep=True
            )
            if data and data["response"]["result"]:
                self.__lock_state = False
            self.__manual_update_time = time.time()

    def is_locked(self):
        """Return whether the charger is closed."""
        return self.__lock_state

    @staticmethod
    def has_battery():
        """Return whether the device has a battery."""
        return False
