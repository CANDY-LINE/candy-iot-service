# -*- coding: utf-8 -*-

import fcntl
import json
import os
import socket
import select
import struct
import sys
import termios
import threading
import time
import subprocess
import atexit
import re

# sys.argv[0] ... Serial Port
# sys.argv[1] ... The path to socket file, e.g. /var/run/candy-iot.sock
# sys.argv[2] ... The network interface name to be monitored

class Monitor(threading.Thread):
    def __init__(self, nic):
        super(Monitor, self).__init__()
        self.nic = nic

    def run(self):
        while True:
            err = subprocess.call("route | grep default | grep %s" % self.nic, shell=True)
            if err != 0:
                my_udhcpc_pid_cmd = "ps | grep \"udhcpc -i %s\" | grep -v \"grep\" | xargs | cut -f 1 -d ' '" % self.nic
                my_udhcpc_pid = subprocess.Popen(my_udhcpc_pid_cmd, shell=True, stdout=subprocess.PIPE).stdout.read()
                if my_udhcpc_pid:
                    subprocess.call("kill -9 %s" % my_udhcpc_pid, shell=True)
                subprocess.call("udhcpc -i %s" % self.nic, shell=True)
            time.sleep(5)

# SerialPort class was imported from John Wiseman's https://github.com/wiseman/arduino-serial/blob/master/arduinoserial.py

# Map from the numbers to the termios constants (which are pretty much
# the same numbers).

BPS_SYMS = {
    4800:     termios.B4800,
    9600:     termios.B9600,
    19200:    termios.B19200,
    38400:    termios.B38400,
    57600:    termios.B57600,
    115200: termios.B115200
    }


# Indices into the termios tuple.

IFLAG = 0
OFLAG = 1
CFLAG = 2
LFLAG = 3
ISPEED = 4
OSPEED = 5
CC = 6


def bps_to_termios_sym(bps):
    return BPS_SYMS[bps]

# For local debugging:
# import server_main
# serial = server_main.SerialPort("/dev/ttyUSB1", 115200)
# server = server_main.SockServer("/var/run/candy-iot.sock", serial)
# server.debug = True
# server.apn_ls()
class SerialPort:

    def __init__(self, serialport, bps):
        """Takes the string name of the serial port
        (e.g. "/dev/tty.usbserial","COM1") and a baud rate (bps) and
        connects to that port at that speed and 8N1. Opens the port in
        fully raw mode so you can send binary data.
        """
        self.fd = os.open(serialport, os.O_RDWR | os.O_NOCTTY | os.O_NDELAY)
        attrs = termios.tcgetattr(self.fd)
        bps_sym = bps_to_termios_sym(bps)
        # Set I/O speed.
        attrs[ISPEED] = bps_sym
        attrs[OSPEED] = bps_sym

        # 8N1
        attrs[CFLAG] &= ~termios.PARENB
        attrs[CFLAG] &= ~termios.CSTOPB
        attrs[CFLAG] &= ~termios.CSIZE
        attrs[CFLAG] |= termios.CS8
        # No flow control
        attrs[CFLAG] &= ~termios.CRTSCTS

        # Turn on READ & ignore contrll lines.
        attrs[CFLAG] |= termios.CREAD | termios.CLOCAL
        # Turn off software flow control.
        attrs[IFLAG] &= ~(termios.IXON | termios.IXOFF | termios.IXANY)

        # Make raw.
        attrs[LFLAG] &= ~(termios.ICANON | termios.ECHO | termios.ECHOE | termios.ISIG)
        attrs[OFLAG] &= ~termios.OPOST

        # It's complicated--See
        # http://unixwiz.net/techtips/termios-vmin-vtime.html
        attrs[CC][termios.VMIN] = 0;
        attrs[CC][termios.VTIME] = 20;
        termios.tcsetattr(self.fd, termios.TCSANOW, attrs)

    def read_until(self, until):
        buf = ""
        done = False
        while not done:
            n = os.read(self.fd, 1)
            if n == '':
                # FIXME: Maybe worth blocking instead of busy-looping?
                time.sleep(0.01)
                continue
            buf = buf + n
            if n == until:
                done = True
        return buf

    def read_line(self):
        try:
            return self.read_until("\n").strip()
        except OSError:
            return None

    def write(self, str):
        os.write(self.fd, str)

    def write_byte(self, byte):
        os.write(self.fd, chr(byte))

class SockServer(threading.Thread):
    def __init__(self, version, sock_path, apn, serial=None):
        super(SockServer, self).__init__()
        self.version = version
        self.sock_path = sock_path
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.serial = serial
        self.debug = False
        if apn:
            self.apn_set(apn['apn'], apn['user'], apn['password'])

    def recv(self, connection, size):
        ready, _, _ = select.select([connection], [], [], 5)
        if ready:
            return connection.recv(size)
        else:
            raise IOError("recv Timeout")

    def run(self):
        self.sock.bind(self.sock_path)
        self.sock.listen(1)
        header_packer = struct.Struct("I")
        print("Listening to the socket[%s]...." % self.sock_path)

        while True:
            try:
                connection, client_address = self.sock.accept()
                print("Accepted from [%s]" % client_address)
                connection.setblocking(0)

                # request
                header = self.recv(connection, header_packer.size)
                size = header_packer.unpack(header)
                unpacker_body = struct.Struct("%is" % size)
                cmd_json = self.recv(connection, unpacker_body.size)
                cmd = json.loads(cmd_json)

                # response
                message = self.perform(cmd)
                if message:
                    size = len(message)
                else:
                    size = 0
                packed_header = header_packer.pack(size)
                connection.sendall(packed_header)
                if size > 0:
                    packer_body = struct.Struct("%is" % size)
                    packed_message = packer_body.pack(message)
                    connection.sendall(packed_message)

            finally:
                if 'connection' in locals():
                    connection.close()

    def perform(self, cmd):
        if cmd['category'] == "apn":
            if cmd['action'] == "ls":
                return self.apn_ls()
            elif cmd['action'] == "set":
                return self.apn_set(cmd['name'], cmd['user_id'], cmd['password'])
        elif cmd['category'] == "network":
            if cmd['action'] == "show":
                return self.network_show()
        elif cmd['category'] == "sim":
            if cmd['action'] == "show":
                return self.sim_show()
        elif cmd['category'] == "modem":
            if cmd['action'] == "show":
                return self.modem_show()
        elif cmd['category'] == "info":
            if cmd['action'] == "version":
                return self.info_version()

        return "Unknown Command"

    def read_line(self):
        line = self.serial.read_line()
        if self.debug:
            print("[modem:IN] => [%s]" % line)
        return line

    def send_at(self, cmd):
        line = "%s\r" % cmd
        if self.debug:
            print("[modem:OUT] => [%s]" % line)
        self.serial.write(line)
        time.sleep(0.1)
        self.read_line() # echo back
        self.read_line() # empty line
        self.read_line() # empty line
        result = ""
        status = None
        while not status:
            line = self.read_line()
            if line == "OK" or line == "ERROR":
                status = line
            elif line is None:
                status = "UNKNOWN"
            elif line.strip() != "":
                result += line + "\n"
        if self.debug:
            print("cmd:[%s] => status:[%s], result:[%s]" % (cmd, status, result))
        return (status, result.strip())

    def apn_ls(self):
        status, result = self.send_at("AT+CGDCONT?")
        apn_list = []
        if status == "OK":
            name_list = map(lambda e: e[10:].split(",")[2].translate(None, '"'), result.split("\n"))
            status, result = self.send_at("AT$QCPDPP?")
            creds_list = []
            if status == "OK":
                creds_list = map(lambda e: e[2].translate(None, '"'),
                    filter(lambda e: len(e) > 2,
                        map(lambda e: e[9:].split(","), result.split("\n"))))
            for i in range(len(name_list)):
                apn = {
                    'apn': name_list[i]
                }
                if i < len(creds_list):
                    apn['user'] = creds_list[i]
                apn_list.append(apn)
        message = {
            'status': status,
            'result': {
                'apns': apn_list
            }
        }
        return json.dumps(message)

    def apn_set(self, name, user_id, password):
        status, result = self.send_at("AT+CGDCONT=1,\"IPV4V6\",\"%s\",\"0.0.0.0\",0,0" % name)
        if status == "OK":
            status, result = self.send_at("AT$QCPDPP=1,3,\"%s\",\"%s\"" % (password, user_id))
        message = {
            'status': status,
            'result': result
        }
        return json.dumps(message)

    def network_show(self):
        status, result = self.send_at("AT+CSQ")
        rssi = ""
        network = "UNKNOWN"
        rssi_desc = ""
        if status == "OK":
            rssi_level = int(result[5:].split(",")[0])
            if rssi_level == 0:
                rssi = "-113"
                rssi_desc = "OR_LESS"
            elif rssi_level == 1:
                rssi = "-111"
            elif rssi_level <= 30:
                rssi = "%i" % (-109 + (rssi_level - 2) * 2)
            elif rssi_level == 31:
                rssi = "-51"
                rssi_desc = "OR_MORE"
            else:
                rssi_desc = "NO_SIGANL"
            status, result = self.send_at("AT+CPAS")
            if status == "OK":
                state_level = int(result[6:])
                if state_level == 4:
                    network = "ONLINE"
                else:
                    network = "OFFLINE"
        message = {
            'status': status,
            'result': {
                'rssi': rssi,
                'rssiDesc': rssi_desc,
                'network': network
            }
        }
        return json.dumps(message)

    def sim_show(self):
        state = "SIM_STATE_ABSENT"
        msisdn = ""
        imsi = ""
        status, result = self.send_at("AT+CIMI")
        if status == "OK":
            imsi = result
            state = "SIM_STATE_READY"
            status, result = self.send_at("AT+CNUM")
            msisdn = result[6:].split(",")[1].translate(None, '"')
        message = {
            'status': status,
            'result': {
                'msisdn': msisdn,
                'imsi': imsi,
                'state': state
            }
        }
        return json.dumps(message)

    def modem_show(self):
        status, result = self.send_at("ATI")
        man = "UNKNOWN"
        mod = "UNKNOWN"
        rev = "UNKNOWN"
        imei = "UNKNOWN"
        if status == "OK":
            info = result.split("\n")
            man = info[0][14:]
            mod = info[1][7:]
            rev = info[2][10:]
            imei = info[3][6:]
        message = {
            'status': status,
            'result': {
                'manufacturer': man,
                'model': mod,
                'revision': rev,
                'imei': imei,
            }
        }
        return json.dumps(message)

    def info_version(self):
        message = {
            'status': 'OK',
            'result': {
                'version': self.version,
            }
        }
        return json.dumps(message)

def delete_sock_path(sock_path):
    try:
        os.unlink(sock_path)
    except OSError:
        if os.path.exists(sock_path):
            raise

def resolve_version():
    if 'VERSION' in os.environ:
        return os.environ['VERSION']
    return 'N/A'

def resolve_boot_apn():
    dir = os.path.dirname(os.path.abspath(__file__))
    apn_json = dir + '/boot-apn.json'
    if not os.path.isfile(apn_json):
        return None
    with open(apn_json) as apn_creds:
        apn = json.load(apn_creds)
    os.remove(apn_json)
    return apn

def main(serial_port, sock_path, nic):
    delete_sock_path(sock_path)
    atexit.register(delete_sock_path, sock_path)

    monitor = Monitor(nic)
    monitor.start()

    if 'EMULATE_SERIALPORT' in os.environ and os.environ['EMULATE_SERIALPORT'] == "1":
        print("Enabling SerialPort emulation...")
        from emulator_serialport import SerialPortEmurator
        serial = SerialPortEmurator()
    else:
        serial = SerialPort(serial_port, 115200)

    server = SockServer(resolve_version(), sock_path, resolve_boot_apn(), serial)
    if 'DEBUG' in os.environ and os.environ['DEBUG'] == "1":
        server.debug = True
    server.start()

    monitor.join()
    server.join()

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("USB Ethernet Network Interface isn't ready. Shutting down.")
    else:
        print("serial_port:%s, sock_path:%s, nic:%s" % (sys.argv[1], sys.argv[2], sys.argv[3]))
        main(sys.argv[1], sys.argv[2], sys.argv[3])
