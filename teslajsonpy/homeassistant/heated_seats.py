#  SPDX-License-Identifier: Apache-2.0
"""
Python Package for controlling Tesla API.

For more details about this api, please refer to the documentation at
https://github.com/zabuldon/teslajsonpy
"""
import time

from typing import Dict, Optional, Text
from teslajsonpy.homeassistant.vehicle import VehicleDevice
from teslajsonpy.homeassistant.climate import Climate

seat_id_map = {
    "left": 0,
    "right": 1,
    "rear_left": 2,
    "rear_center": 4,
    "rear_right": 5,
}

seat_heat_map = {
    0: "Off",
    1: "Low",
    2: "Medium",
    3: "High",
}

class HeatedSeat(VehicleDevice):
    """Home-assistant heated seat class for Tesla vehicles.

    This is intended to be partially inherited by a Home-Assitant entity.
    """

    def __init__(self, data, controller):
        """Initialize a heated seat for the vehicle.

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
        self.__climate = Climate(data, controller)
        self.__manual_update_time = 0
        self.__seat_heat_level = None
        self.__seats_are_on = False
        self.__seat_name = None
        self._sensor_type: Optional[Text] = None

        self.type = f"heated seat"
        self.hass_type = "binary_sensor"

        self.name = self._name()

        self.uniq_name = self._uniq_name()
        self.bin_type = 0x7

    async def async_update(self, wake_if_asleep=False, force=False) -> None:
        """Update the seat state."""
        await super().async_update(wake_if_asleep=wake_if_asleep)
        self.refresh()

    def refresh(self) -> None:
        """Refresh data.

        This assumes the controller has already been updated
        """
        super().refresh()
        last_update = self._controller.get_last_update_time(self._id)
        if last_update >= self.__manual_update_time:
            data = self._controller.get_climate_params(self._id)
            self.__seats_are_on = (
                any(
                    [
                        data["seat_heater_left"],
                        data["seat_heater_right"],
                        data["seat_heater_rear_left"],
                        data["seat_heater_rear_center"],
                        data["seat_heater_rear_right"],
                    ]
                 ) if data else False
            )

    async def set_value(self, level):
        """Set heated seat level."""
        if not self.__climate.is_hvac_enabled:
            await self.__climate.set_status(True)

        numeric_level = [k for k, v in seat_heat_map.items() if v == level]

        data = await self._controller.command(
            self._id,
            "remote_seat_heater_request",
            data={"heater": seat_id_map[self.__seat_name], "level": level},
            wake_if_asleep=True,
        )
        if data and data["response"]["result"]:
            self.__seat_heat_level = seat_heat_map[level]
        self.__manual_update_time = time.time()

    def get_value(self):
        """Return current heated seat level."""
        return self.__seats_are_on

    @staticmethod
    def has_battery():
        """Return whether the device has a battery."""
        return False

    @property
    def sensor_type(self) -> Optional[Text]:
        """Return the sensor_type for use by HA as a device_class."""
        return self._sensor_type
