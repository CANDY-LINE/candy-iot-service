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
  4800:   termios.B4800,
  9600:   termios.B9600,
  19200:  termios.B19200,
  38400:  termios.B38400,
  57600:  termios.B57600,
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


class SerialPortEmurator:
  def __init__(self):
    self.res = {
      'AT+CGDCONT?': [
        "(ECHO_BACK)",
        "",
        "",
        "+CGDCONT: 1,\"IPV4V6\",\"access_point_name\",\"0.0.0.0\",0,0",
        "",
        "OK",
        ""
      ],
      'AT$QCPDPP?': [
        "(ECHO_BACK)",
        "",
        "",
        "$QCPDPP: 1,3,\"user_id\"",
        "$QCPDPP: 2,0",
        "$QCPDPP: 3,0",
        "$QCPDPP: 4,0",
        "$QCPDPP: 5,0",
        "$QCPDPP: 6,0",
        "$QCPDPP: 7,0",
        "$QCPDPP: 8,0",
        "$QCPDPP: 9,0",
        "$QCPDPP: 10,0",
        "$QCPDPP: 11,0",
        "$QCPDPP: 12,0",
        "$QCPDPP: 13,0",
        "$QCPDPP: 14,0",
        "$QCPDPP: 15,0",
        "$QCPDPP: 16,0",
        "",
        "OK",
        ""
      ],
      'AT+CGDCONT=': [
        "(ECHO_BACK)",
        "",
        "",
        "OK",
        ""
      ],
      'AT$QCPDPP=': [
        "(ECHO_BACK)",
        "",
        "",
        "OK",
        ""
      ]
    }

  def read_line(self):
    if self.line < 0:
      return None
    try:
      text = self.res[self.cmd][self.line]
      self.line += 1
      return text
    except:
      self.line = -1
      return None

  def write(self, str):
    print("W:[%s]" % str)
    self.cmd = str.strip()
    if self.cmd.find('=') >= 0:
      self.cmd = self.cmd[:self.cmd.find('=') + 1]
    self.line = 0
    self.res[self.cmd][0] = str.strip()


class SockServer(threading.Thread):
  def __init__(self, sock_path, serial=None):
    super(SockServer, self).__init__()
    self.sock_path = sock_path
    self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    self.serial = serial
  
  def recv(self, connection, size):
    ready = select.select([connection], [], [], 5)
    if ready[0]:
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
    
    return "Unknown Command"

  def send_at(self, cmd):
    self.serial.write("%s\r\n" % cmd)
    self.serial.read_line() # echo back
    self.serial.read_line() # empty line
    self.serial.read_line() # empty line
    result = ""
    status = None
    while not status:
      line = self.serial.read_line()
      if line == "OK" or line == "ERROR":
        status = line
      elif line is None:
        status = "Unknown"
      elif line.strip() != "":
        result += line + "\n"
    return (status, result.strip())

  def apn_ls(self):
    status, result = self.send_at("AT+CGDCONT?")
    if status == "OK":
      apn_list = result.split("\n")
      status, result = self.send_at("AT$QCPDPP?")
      if status == "OK":
        result = {
          'apn_list': apn_list,
          'creds_list': result.split("\n")
        }
      else:
        result = {
          'apn_list': apn_list,
          'result': result
        }
    message = {
      'status': status,
      'result': result
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

def delete_sock_path(sock_path):
  try:
    os.unlink(sock_path)
  except OSError:
    if os.path.exists(sock_path):
      raise

def main(serial_port, sock_path, nic):
  delete_sock_path(sock_path)
  atexit.register(delete_sock_path, sock_path)

  monitor = Monitor(nic)
  monitor.start()

  serial = SerialPort(serial_port, 115200)
  server = SockServer(sock_path, serial)
  server.start()

  monitor.join()
  server.join()

if __name__ == '__main__':
  if len(sys.argv) < 3:
    print("USB Ethernet Network Interface isn't ready. Shutting down.")
  else:
    print("serial_port:%s, sock_path:%s, nic:%s" % (sys.argv[1], sys.argv[2], sys.argv[3]))
    main(sys.argv[1], sys.argv[2], sys.argv[3])
