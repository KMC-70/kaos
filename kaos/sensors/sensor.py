"""
This file defines a Sensor class. It represents a sensor object.

Author: Team KMC-70.
"""

from flask import Blueprint

class Sensor(object):
    """
    A Sensor object which represents a real-world sensor on a satellite.
    The attributes here are not set in stone and can change according to
    changes in the client's sensor models.

    TODO: confirm these attribute descriptions. Most attribute descriptions can be found here:
    http://help.agi.com/stk/index.htm#stk/ObjectMap_Sensor.htm%3FTocPath%3DGetting%2520Started%7CBuild%2520a%2520Scenario%7CAdd%2520STK%2520Objects%7CObject%2520Properties%7CSensors%7C_____0

    Attributes:
        sensor_id: unique sensor ID specifying the type of sensor.
        agile: TODO: what is this?
        beam_mode_type: TODO: what is this?
        center_boresight_pitch_angle: sensor pitch angle.
        center_boresight_roll_angle: sensor roll angle
        dollar_cost: cost of sensor in dollars. TODO: is this necessary?
        maneuver_speed: speed of sensor maneuverability.
        name: sensor name (manufacturer name)
        platform_id:
        pointing_conic_half_angle: half-angle of sensor's conic view
        pointing_horizontal_half_angle: The angle from the boresight (Z) direction to the
                                        edge of the sensor in the XZ plane of the sensor's coordinate system.
        pointing_vertical_half_angle: The angle from the boresight (Z) direction to the
                                        edge of the sensor in the YZ plane of the sensor's coordinate system.
        scene_duration: duration of viewing scene.
        sensor_pointing_type: pointing type of the sensor. E.g. 3D model, along vector, fixed etc.
        sensor_type: type of field of view of the sensor. E.g. Complex conic, custom, rectangular etc.
        stabilization_time:
        view_horizontal_half_angle: The angle from the boresight (Z) direction to the
                                    edge of the sensor in the XZ plane of the sensor's coordinate system.
        view_vertical_half_angle: The angle from the boresight (Z) direction to the
                                    edge of the sensor in the YZ plane of the sensor's coordinate system.

    Example attribute string (Note that the attributes of this string are out of order with the above):

    '831cf482-b37b-4468-83cd-659814256892',true,,'0','0','100','1',
    'WV110','41fe7f26-c557-49eb-aec8-dd658966f3a6','40.6','-1','-1','0',0,1,'1','2','0.6'
    """
    def __init__(self,
                sensor_id,
                agile=True,
                beam_mode_type,
                center_boresight_pitch_angle,
                center_boresight_roll_angle,
                dollar_cost,
                maneuver_speed,
                name,
                platform_id,
                pointing_conic_half_angle,
                pointing_horizontal_half_angle,
                pointing_vertical_half_angle,
                scene_duration,
                sensor_pointing_type,
                sensor_type,
                stabilization_time,
                view_horizontal_half_angle,
                view_vertical_half_angle):

        self.sensor_id                          = sensor_id
        self.agile                              = agile
        self.beam_mode_type                     = beam_mode_type
        self.center_boresight_pitch_angle       = center_boresight_pitch_angle
        self.center_boresight_roll_angle        = center_boresight_roll_angle
        self.dollar_cost                        = dollar_cost
        self.maneuver_speed                     = maneuver_speed
        self.name                               = name
        self.platform_id                        = platform_id
        self.pointing_conic_half_angle          = pointing_conic_half_angle
        self.pointing_horizontal_half_angle     = pointing_horizontal_half_angle
        self.pointing_vertical_half_angle       = pointing_vertical_half_angle
        self.scene_duration                     = scene_duration
        self.sensor_pointing_type               = sensor_pointing_type
        self.sensor_type                        = sensor_type
        self.stabilization_time                 = stabilization_time
        self.view_horizontal_half_angle         = view_horizontal_half_angle
        self.view_vertical_half_angle           = view_vertical_half_angle


