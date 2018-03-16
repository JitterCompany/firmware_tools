#!/usr/bin/env python

import time
import select
import socket
import sys
import os.path
import argparse


def list_to_str(l, sep=','):
    ret = ""
    for i in l:
        ret+= str(i) + sep
    
    if len(ret):
        ret = ret[:-1]

    return ret

def parse_list(l):
    ret = []
    for v in l.split(','):
        val = v.strip()
        if len(val):
            ret.append(val)

    return ret

def encode(string):
    return bytes(string, 'ascii')

def decode(bytestr):
    return str(bytestr, 'ascii')

def print_devices(devices):
    for dev in devices:
        print("\t{}".format(dev))
    print('')

class Update:

    def __init__(self, firmware_file_m0, firmware_file_m4, host, port):
        self.devices = []
        self.updated = []
        self.firmware_file_m0 = firmware_file_m0
        self.firmware_file_m4 = firmware_file_m4

        self.server_host = host
        self.server_port = port

    def parse_incoming(self, socket, timeout_sec=10):

        ready = select.select([socket], [], [], timeout_sec)
        timeout = True
        if ready[0]:
            response = decode(socket.recv(1024*1024))
            if len(response):
                timeout = False

                for line in response.split("\n"):
                    tokens = line.split('=')
                    if len(tokens) < 2:
                        continue
                    key = tokens[0]
                    value = line[len(key):].strip('=')

                    if key == 'devices':
                        self.devices = parse_list(value)

                    if key == 'updated':
                        self.updated = parse_list(value)

        if timeout:
            print("ERROR: timeout")
            return False
        return True


    def ui_select_devices(self):
        """ UI: show devices / select which devices to update """

        to_update = self.devices
        print("")
        if not len(self.devices):
            print("ERROR: No device(s) available for update!")
            return []

        elif len(self.devices) == 1:
            print("Updating device {}".format(self.devices[0]))

        else:
            print("Device(s) available for update:")
            print_devices(self.devices)
            
            # TODO maybe a way to select which ones to update
            # and / or ENTER to update all?
        
        # always update all devices for now
        return to_update
   

    def ui_result(self):
        """ UI: show the result(s) of the update(s)"""
        failed = []
        for dev in self.devices:
            if not dev in self.updated:
                failed.append(dev)
        
        if len(failed):
            print("ERROR: Failed to update these devices:")
            print_devices(failed)

        elif len(self.devices):
            print("SUCCESS: All devices updated")

        else:
            print("ERROR: No device(s) available for update!")

        # TODO these could be tried again if the user selects it
        self.devices = failed

    def upload(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            try:
                # connect and get device list
                sock.connect((self.server_host, self.server_port))
                if not self.parse_incoming(sock, 2):
                    return
                
                # select which devices to update
                to_update = self.ui_select_devices()
                if not len(to_update):
                    return
                
                # send update commands
                commands = []
                commands.append("update_devices=" + list_to_str(to_update))
                if self.firmware_file_m0 is not None:
                    commands.append("fw_m0=" + self.firmware_file_m0)
                else:
                    print("Note: no m0 firmware found")
                commands.append("fw_m4=" + self.firmware_file_m4)
                sock.sendall(encode(list_to_str(commands, '\n')))
                
                # get list of updated devices
                if not self.parse_incoming(sock, 2+10*len(to_update)):
                    return

                self.ui_result()

            except ConnectionRefusedError:
                print("ERROR: Update server not running!")

class Program:
    
    def __init__(self):
        parser = argparse.ArgumentParser(description="Connects to a running \
                firmware update server to update a target with a given \
                firmware. Either specify --config or <firmware> <firmware2>")
        parser.add_argument("--config",  help="A config file specifying one \
                target per line. Any data up to the first whitespace (if any)\
                is parsed as the firmware filename")
        parser.add_argument("firmware", nargs='?', help="The firmware file \
                to send to the device")
        parser.add_argument("firmware2", nargs='?',  help="The secondary \
                firmware file to send to the device")
        parser.add_argument("-ip","--ip", type=str, help="The update server ip \
                address to connect to (default=localhost)", default="localhost")
        parser.add_argument("-p","--port", type=int, help="The update server \
                port to connect to (default=3853)", default=3853)

        self.parser = parser
        self.args = None


    def parse_args(self):
        args = self.parser.parse_args()
        self.args = args

        updates = {}
        if not args.config is None:
            try:
                with open(args.config, 'r') as cfg:
                    for line in cfg.readlines():
                        opts = line.split()
                        updates[opts[3]] = opts[0]

            except IOError:
                print("ERROR: failed to open config file '%s'"
                        % args.config)
                sys.exit()
            
            if not len(updates):
                print("ERROR: no valid target(s) found in config file '%s'"
                        % args.config)
                self.parser.print_usage()
                sys.exit()
                
        else:
            if (args.firmware is None 
                    or args.firmware2 is None):

                print("ERROR: specify at least --config or firmware, firmware2")
                self.parser.print_usage()
                sys.exit()
            else:
                updates['43xx_m0'] = args.firmware
                updates['43xx_m4'] = args.firmware2

        return updates


    def run(self):
        
        updates = self.parse_args()
        
        files = {'43xx_m0': None}
        for key in updates:
            f = updates[key]
            if not os.path.isfile(f):
                print("ERROR: {} is not a file".format(f))
                self.parser.print_usage()
                sys.exit()

            files[key] = f


        update = Update(files['43xx_m0'], files['43xx_m4'], self.args.ip, self.args.port)
        update.upload()

if __name__ == "__main__":
    program = Program()
    program.run()



