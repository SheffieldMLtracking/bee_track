import time
import datetime
import RPi.GPIO as GPIO
from configurable import Configurable
import multiprocessing
from pathlib import Path

class Trigger(Configurable):
    def __init__(self,message_queue,cam_trigger,t=2.0):
        super().__init__(message_queue)
        print("Initialising Trigger Control")  
        self.cam_trigger = cam_trigger
        self.debug = False
        self.manager = multiprocessing.Manager()
        self.flashselection = self.manager.list()
        self.flash_power_sel = self.manager.list()

        self.index = multiprocessing.Value('i',0)
        self.record = self.manager.list()
        self.direction = 0

        self.all_flash_pins = [14,15,18,23,27,17]
        self.flash_select_pins = self.all_flash_pins #[8,10,12,16] #Board->BCM pins

        self.power_control_pins = [26,20,21]
        try:
            relay_default = int(open(str(Path.home())+'/bee_track/webinterface/relay_default.txt','r').read())
        except:
            relay_default = 1 #if there is no text file to tell us the relay setting, we assum it's set to on by default
        if relay_default==1:
            self.logic_states=[True, False] #If flash relays off by default, use [True, False]; if flash relays on by default, use [False, True]
        else:
            self.logic_states=[False, True]
        self.power_states = [self.logic_states[1], self.logic_states[1], self.logic_states[1]]
        self.flash_off_time = self.manager.Value('f',0)
        self.max_flashes = 55

        self.trigger_pin = 24 #18 #Board->BCM pins
        times_fired = []
        for i in range(len(self.flash_select_pins)):
            self.flashselection.append(i)
            times_fired.append(0)

        self.times_fired = self.manager.Array('i',times_fired)

        self.flash_power_sel.append(0) # top
        self.flash_power_sel.append(1) # bottom

        self.t = multiprocessing.Value('d',t)
        self.ds = multiprocessing.Value('d',0)
        self.flashseq = multiprocessing.Value('i',0) #0 = flash all, 1 = flash 2 at a time, 1 = flash in sequence,
        self.skipnoflashes = multiprocessing.Value('i',0) #how many to skip
        self.total_flashes = multiprocessing.Value('i',0)
        self.preptime = 0.02
        self.triggertime = 0.03 #this will end up at least 200us
        self.seqn = 0
        GPIO.setmode(GPIO.BCM) #GPIO.BOARD) #Board->BCM
        GPIO.setup(self.trigger_pin, GPIO.OUT)

        for pin in self.flash_select_pins:
            GPIO.setup(pin, GPIO.OUT)

        time.sleep(0.5)
        for pin in self.flash_select_pins:
            GPIO.output(pin, False)

        for pin in self.power_control_pins:
            GPIO.setup(pin, GPIO.OUT)
            GPIO.output(pin, self.logic_states[1])
            time.sleep(4)

        GPIO.output(self.trigger_pin, False)
        print("Running")
        self.run = multiprocessing.Event()
    
    def trigger_camera(self,fireflash,endofset):
        """
            Send trigger to camera (and flash)
            fireflash = boolean: true=fire flash
            endofset = boolean: whether this is the last photo of a set (this will then tell the tracking system to look for the bee).
        """

        self.update_power_pins()
        if self.debug:
            print("Photo:    Flash" if fireflash else "Photo: No Flash")
        if self.seqn>=len(self.flashselection):
                    self.seqn = 0
        if fireflash:
            if self.flashseq.value==0:
                for flash in self.flashselection:
                    GPIO.output(self.flash_select_pins[flash],True)
                    self.times_fired[flash] += 1
                    self.total_flashes.value += 1
            if self.flashseq.value==1:
                if self.seqn>=len(self.flashselection)-1:
                    self.seqn = 0
                GPIO.output(self.flash_select_pins[self.flashselection[self.seqn]],True)
                GPIO.output(self.flash_select_pins[self.flashselection[self.seqn+1]],True)
                self.times_fired[self.seqn] += 1
                self.times_fired[self.seqn+1] += 1
                self.total_flashes.value += 1
                self.seqn+=2
                if self.seqn>=len(self.flashselection):
                    self.seqn = 0
            if self.flashseq.value==2:
                GPIO.output(self.flash_select_pins[self.flashselection[self.seqn]],True)
                self.times_fired[self.seqn] += 1
                self.total_flashes.value += 1
                self.seqn+=1
                if self.seqn>=len(self.flashselection):
                    self.seqn = 0

            if self.flashseq.value==4:
                if self.seqn>=len(self.flashselection)-1:
                    self.seqn = 0
                GPIO.output(self.flash_select_pins[self.flashselection[self.seqn]],True)
                GPIO.output(self.flash_select_pins[self.flashselection[self.seqn+1]],True)
                self.times_fired[self.seqn] += 1
                self.times_fired[self.seqn+1] += 1
                self.seqn+=2
                if self.seqn>=len(self.flashselection):
                    self.seqn = 0

                GPIO.output(self.flash_select_pins[self.flashselection[self.seqn]],True)
                GPIO.output(self.flash_select_pins[self.flashselection[self.seqn+1]],True)
                self.times_fired[self.seqn] += 1
                self.times_fired[self.seqn+1] += 1
                self.seqn+=2
                if self.seqn>=len(self.flashselection):
                    self.seqn = 0

                self.total_flashes.value += 1

            if self.flashseq.value==9:
                for pin in self.flash_select_pins:
                    GPIO.output(pin, False)
        else:
            for pin in self.flash_select_pins:
                GPIO.output(pin, False)

        time.sleep(self.preptime)
        triggertime = time.time() #TODO Why are these two different?
        triggertimestring = datetime.datetime.now() #need to convert to string later
        
        triggertimestring = triggertimestring.strftime("%Y%m%d_%H:%M:%S.%f")
        self.record.append({'index':self.index.value,'endofset':endofset,'direction':self.direction,'flash':fireflash,
            'flashselection':list(self.flashselection),'triggertime':triggertime,'triggertimestring':triggertimestring})
        print("Incrementing trigger index from %d" % self.index.value) 
        self.index.value = self.index.value + 1
        #Software trigger...
        #self.cam_trigger.set()
        
        
        #Trigger via pin...
        GPIO.output(self.trigger_pin,True)
        time.sleep(self.triggertime)
        for pin in self.flash_select_pins:
            GPIO.output(pin, False)
            
        #(trigger via pin)...
        GPIO.output(self.trigger_pin,False)

    def update_power_pins(self):
        print(self.times_fired)
        if self.times_fired[0] >= self.max_flashes:
            print("STARTED POWER CYCLE")
            #start off cycle, top off!!!
            self.power_states[0] = self.logic_states[0]
            self.times_fired[0] = 0
            self.times_fired[1] = 0
            self.flash_off_time.value = time.time()
            self.seqn = 0
            self.flashselection = self.manager.Array('i',[2,3,4,5])
            # remove top flashes from flash select pins
        elif self.power_states[0] == self.logic_states[0] and (time.time() - self.flash_off_time.value) > 3:
            #Top back on, middle off
            self.power_states[0] = self.logic_states[1]
            self.power_states[1] = self.logic_states[0]
            self.times_fired[2] = 0
            self.times_fired[3] = 0
            self.flash_off_time.value = time.time()
            self.seqn = 0
            self.flashselection = self.manager.Array('i',[0,1,4,5])
            #Add top flashes back
        elif self.power_states[1] == self.logic_states[0] and (time.time() - self.flash_off_time.value) > 3:
            #Middle back on, bottom off
            self.power_states[1] = self.logic_states[1]
            self.power_states[2] = self.logic_states[0]

            self.flash_off_time.value = time.time()
            self.flashselection = self.manager.Array('i',[0,1,2,3])
            self.seqn = 0
        elif self.power_states[2] == self.logic_states[0] and (time.time() - self.flash_off_time.value) > 3:
            #Bottom nack on, is_off_cycle to false
            self.power_states[2] = self.logic_states[1]
            #times fired to zero
            self.flashselection = self.manager.Array('i',[0,1,2,3,4,5])
            self.seqn = 0
            print("FINISHED POWER CYCLE")
            self.times_fired[4] = 0
            self.times_fired[5] = 0
        elif self.power_states[0] == self.logic_states[1] and self.power_states[1] == self.logic_states[1] and self.power_states[2] == self.logic_states[1]:
            self.flashselection = self.manager.Array('i',[0,1,2,3,4,5])
            self.power_states = [self.logic_states[1], self.logic_states[1], self.logic_states[1]]

        for (pin,power) in zip(self.power_control_pins, self.power_states):
            GPIO.output(pin,power)

    def worker(self):
        skipcount = 0
        while (True):
            self.run.wait()
            delaystart = self.ds.value*self.t.value
            time.sleep(delaystart)
            skipcount+=1
            skipnoflashphoto = (skipcount<=self.skipnoflashes.value)
            self.trigger_camera(True,skipnoflashphoto)
            if not skipnoflashphoto:
                self.trigger_camera(False,True)
                skipcount = 0
                time.sleep(self.t.value-self.triggertime*2-self.preptime*2-delaystart)
            else:
                time.sleep(self.t.value-self.triggertime-self.preptime-delaystart)
