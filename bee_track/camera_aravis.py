"""
This module contains the Aravis Camera class.
"""

import logging
import gc
import os

import numpy as np
# TODO what's this gi.repository?
# PyGObject https://gnome.pages.gitlab.gnome.org/pygobject/
from gi.repository import Aravis

from bee_track.camera import Camera

logger = logging.getLogger(__name__)


class AravisCamera(Camera):
    """
    Aravis Camera interface

    https://lazka.github.io/pgi-docs/Aravis-0.8/
    """

    @classmethod
    def update_device_list(cls):
        """
        Detect devices
        """
        # Updates the list of currently online devices.
        # https://lazka.github.io/pgi-docs/Aravis-0.8/functions.html#Aravis.update_device_list
        Aravis.update_device_list()

    @classmethod
    def get_n_devices(cls) -> int:
        """
        Retrieves the number of currently online devices.
        """
        cls.update_device_list()
        # https://lazka.github.io/pgi-docs/Aravis-0.8/functions.html#Aravis.get_n_devices
        n_cams = Aravis.get_n_devices()

        logger.info("%d cameras found" % n_cams)

        return n_cams

    @classmethod
    def get_device_ids(cls) -> list[str]:
        """
        Get camera identifiers
        """
        ids = list()
        for i in range(cls.get_n_devices()):
            # https://lazka.github.io/pgi-docs/Aravis-0.8/functions.html#Aravis.get_device_id
            dev_id: str = Aravis.get_device_id(i)
            logger.info("Found camera: %s" % dev_id)
            ids.append(dev_id)
        return ids

    def setup_camera(self):
        print("PROCESS ID: ", os.getpid())
        os.system("sudo chrt -f -p 1 %d" % os.getpid())
        Aravis.enable_interface("Fake")
        # https://lazka.github.io/pgi-docs/Aravis-0.8/classes/Camera.html
        self.aravis_camera = Aravis.Camera.new(self.cam_id)
        self.width = int(2048)
        self.height = int(1536)

        self.width = int(2048)
        self.height = int(1536)
        self.aravis_camera.set_binning(1, 1)
        self.aravis_camera.set_region(0, 0, self.width, self.height)  # 2064x1544

        # self.width = int(2048/2)
        # self.height = int(1536/2)
        # self.aravis_camera.set_region(0,0,self.width,self.height) #2064x1544
        # self.aravis_camera.set_binning(2,2)

        print("CAMERA NETWORK CONFIGURATION")
        self.aravis_camera.gv_set_packet_size(8000)
        # psize = self.aravis_camera.gv_auto_packet_size()
        # print("Packet size: %d" % psize)
        self.aravis_camera.gv_set_packet_delay(80000)  # (40000) #np.random.randint(10000))
        print("Packet Delay")
        print(self.aravis_camera.gv_get_packet_delay())
        # self.aravis_camera.gv_set_stream_options(Aravis.GvStreamOption.NONE)

        aravis_device = self.aravis_camera.get_device();
        ####print(aravis_device.get_string_feature_value('MaxImageSize'))

        availpixelformats = self.aravis_camera.dup_available_pixel_formats_as_strings()

        if 'BayerRG8' in availpixelformats:
            aravis_device.set_string_feature_value("PixelFormat", "BayerRG8")

        self.colour_camera.value = False
        self.return_full_colour.value = False
        self.pixelformatstring = self.aravis_camera.get_pixel_format_as_string()
        print("-----")
        print("!!" + self.aravis_camera.get_pixel_format_as_string() + "!!")
        print("-----")
        print(self.aravis_camera.get_pixel_format_as_string() == 'BayerRG8')
        if self.aravis_camera.get_pixel_format_as_string() == 'BayerRG8':
            print("Bayer... colour_camera=TRUE, ReturnsFullColour=False")
            self.colour_camera.value = True
            self.return_full_colour.value = False

        if self.aravis_camera.get_pixel_format_as_string() == 'RGB8Packed':
            print("RGB8... colour_camera=TRUE, ReturnsFullColour=True")
            self.colour_camera.value = True
            self.return_full_colour.value = True

        # Trying to get it working...
        # aravis_device.set_string_feature_value("LineSelector", "Line0")
        # aravis_device.set_string_feature_value("LineMode", "Input")

        # Triggering the camera:
        #  Software trigger...    
        # aravis_device.set_string_feature_value("TriggerMode", "On")
        # aravis_device.set_string_feature_value("TriggerSource", "Software")

        #  Hardware trigger...
        aravis_device.set_string_feature_value("TriggerMode", "On")
        aravis_device.set_string_feature_value("TriggerSource", "Line0")

        ##print(aravis_device.get_available_trigger_sources())
        ##print(self.aravis_camera.get_available_pixel_formats_as_strings())
        ##self.aravis_camera.set_trigger("Line0")
        ####### #self.aravis_camera.set_trigger_source("Line0")

        aravis_device.set_string_feature_value("TriggerActivation", "RisingEdge");
        aravis_device.set_string_feature_value("AcquisitionMode", "Continuous");

        # Triggering the flash...
        # if triggerflash: #this camera might not be the one doing the triggering
        aravis_device.set_string_feature_value("LineSelector", "Line2")
        aravis_device.set_boolean_feature_value("StrobeEnable", True)
        aravis_device.set_string_feature_value("LineMode", "Strobe")
        aravis_device.set_integer_feature_value("StrobeLineDelay", 100)
        aravis_device.set_integer_feature_value("StrobeLinePreDelay", 165)  # 200
        aravis_device.set_string_feature_value("LineSource", "ExposureStartActive")
        aravis_device.set_boolean_feature_value("LineInverter", True)

        # aravis_device.set_string_feature_value("ExposureTimeMode","UltraShort")
        self.aravis_camera.set_exposure_time(90)  # 140
        self.aravis_camera.set_gain(0)

        ##########NEW CODE FOR SHORT EXPOSURE##########
        # aravis_device = self.aravis_camera.get_device();
        # aravis_device.set_string_feature_value("ExposureTimeMode","UltraShort")
        # self.aravis_camera.set_exposure_time(7) #15 us
        # self.aravis_camera.set_gain(0)
        # self.aravis_camera.set_pixel_format (Aravis.PIXEL_FORMAT_MONO_8)
        # self.aravis_camera.set_trigger("Line1")
        # aravis_device.set_float_feature_value("LineDebouncerTime",5.0)

        ##########ORIGINAL CODE########################
        # self.aravis_camera.set_exposure_time(15) #1000000)#15 us
        # self.aravis_camera.set_gain(0)
        # self.aravis_camera.set_pixel_format (Aravis.PIXEL_FORMAT_MONO_8)
        # self.aravis_camera.set_trigger("Line1")

        self.payload = self.aravis_camera.get_payload()
        self.stream = self.aravis_camera.create_stream(None, None)
        self.stream.set_property('packet-timeout', 40000)
        self.stream.set_property('packet-request-ratio', 0.25)

        ###

        # self.stream.set_property('packet-timeout',5000)
        # self.stream.set_property('frame-retention',250000)
        # self.stream.set_property('packet-request-ratio',0.1)
        # self.stream.set_property('socket-buffer',Aravis.GvStreamSocketBuffer.FIXED)
        # self.stream.set_property('socket-buffer-size',5000000)
        # self.stream.set_property('packet-resend',Aravis.GvStreamPacketResend.ALWAYS)

        ###

        if self.stream is None:
            print("Failed to construct stream")
            return
        self.aravis_camera.start_acquisition()
        for i in range(0, 16):
            self.stream.push_buffer(Aravis.Buffer.new_allocate(self.payload))

        # Print info about camera...
        print("Camera vendor : %s" % (self.aravis_camera.get_vendor_name()))
        print("Camera model  : %s" % (self.aravis_camera.get_model_name()))
        print("Camera id     : %s" % (self.aravis_camera.get_device_id()))
        print("Pixel format  : %s" % (self.aravis_camera.get_pixel_format_as_string()))

        print("Ready")

    def camera_config_worker(self):
        """
        Listen for new settings/options in the camera configuration queue and set them on the device.
        """
        while True:
            # Wait for a new configuration option to arrive
            config = self.config_camera_queue.get()
            print("Got:", config)
            key = config[0]
            value = config[1]
            match key:
                case 'exposure':
                    self.aravis_camera.set_exposure_time(value)
                case 'delay':
                    aravis_device = self.aravis_camera.get_device()
                    aravis_device.set_integer_feature_value("StrobeLineDelay", value)
                case 'predelay':
                    aravis_device = self.aravis_camera.get_device()
                    aravis_device.set_integer_feature_value("StrobeLinePreDelay", value)
                case _:
                    raise ValueError(config)

    def camera_trigger(self):
        """
        Software camera trigger
        """

        while True:
            if self.debug:
                print("WAITING FOR TRIGGER")
            # Wait for software trigger
            self.cam_trigger.wait()
            if self.debug:
                print("Software Trigger...")
            self.aravis_camera.software_trigger()
            self.cam_trigger.clear()

    def get_photo(self, get_raw: bool = False):
        if self.debug:
            print(self.cam_id, self.stream.get_n_buffers())
            print(self.cam_id, "waiting for photo...")
        buffer = self.stream.pop_buffer()

        if self.debug:
            print(self.cam_id, "got buffer...")

        if buffer is None:
            self.message_queue.put(self.cam_id + " Buffer read failed")
            print(self.cam_id, "buffer read failed")
            gc.collect()
            return None
        status = buffer.get_status()
        if status != 0:
            print(self.cam_id, "Status Error")
            print(self.cam_id, status)
            self.message_queue.put(self.cam_id + " Buffer Error: " + str(status))
            self.stream.push_buffer(buffer)  # return it to the buffer
            gc.collect()
            return None
        print("Stream statistics")
        print(self.stream.get_statistics())
        if self.debug:
            print(self.cam_id, "buffer ok")

        # Get image data
        raw = np.frombuffer(buffer.get_data(), dtype=np.uint8)
        if not get_raw:
            raw = raw.astype(float)
        self.stream.push_buffer(buffer)
        if bool(self.return_full_colour.value):
            print(">>>")
            new_shape = [self.height, self.width, 3]
        else:
            new_shape = [self.height, self.width]
        return np.reshape(raw, new_shape)

    def close(self):
        """
        shutdown camera, etc
        TODO!
        """
        raise NotImplementedError
