import numpy as np
from bee_track.configurable import Configurable
from btretrodetect import Retrodetect, ColourRetrodetect

class Tracking(Configurable):
    def __init__(self,message_queue,greyscale_photo_queue,colour_photo_queue,scalingfactor=3):
        print("!!!")
        super().__init__(message_queue)
        self.greyscale_photo_queue = greyscale_photo_queue
        self.colour_photo_queue = colour_photo_queue        
        #self.tracking_queue = Queue()         
        self.g_rd = Retrodetect(message_queue=message_queue,scalingfactor=scalingfactor)
        self.c_rd = ColourRetrodetect(patchSize=36,message_queue=message_queue,scalingfactor=scalingfactor)
        self.g_rd.associated_colour_retrodetect = self.c_rd
        #self.track = Value('i',0)
        self.info = False
        self.debug = False
        
    def worker(self):
        self.index = 0
        while True:
            print("Waiting for photos...")
            greyscale_index,greyscale_photoitem = self.greyscale_photo_queue.pop()
            print(" greyscale popped ")
            self.g_rd.process_image(greyscale_photoitem)            
            if self.colour_photo_queue is not None:
                colour_index,colour_photoitem = self.colour_photo_queue.pop()
                print(" colour popped  --> processing.")
                self.c_rd.process_image(colour_photoitem)
            

