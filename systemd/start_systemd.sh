#!/usr/bin/env bash

# Copyright (c) 2016 Robotma.com

MODULE_SUPPORTED=0

function try_to_change_usb_data_conn {
  RET=`lsusb | grep 1ecb:0202`
  RET=$?
  if [ "${RET}" != "0" ]; then
    return
  fi
  # Reset to default
  # echo -e "AT@USBCHG=ACM\r\r" | microcom -t 1000 -s 115200 /dev/ttyUSB1 && echo "*** Rebooting... ***" && reboot
  # Change to ECM
  logger -s "Modifying the USB data connection I/F to ECM"
  echo -e "AT@USBCHG=ECM\r\rAT@AUTOCONN=1\r\r" | microcom -t 1000 -s 115200 /dev/ttyACM0
  logger -s "*** Rebooting... ***"
  reboot
}

function diagnose_self {
  MODULE_IDS="1ecb:0208" # space delimiter

  RET=`dmesg | grep "register 'cdc_ether'"`
  RET=$?
  if [ "${RET}" != "0" ]; then
    try_to_change_usb_data_conn
  fi

  for m in ${MODULE_IDS}
  do
    RET=`lsusb | grep ${m}`
    RET=$?
    if [ "${RET}" == "0" ]; then
      MODULE_SUPPORTED=1
    fi
  done
}

# LTE/3G USB Ethernet
function activate_lte {
  if [ "${MODULE_SUPPORTED}" != "1" ]; then
    return
  fi

  logger -s "Activating LTE/3G Module..."
  IF_NAME=`dmesg | grep "renamed network interface usb1" | sed 's/^.* usb1 to //g'`
  RET=$?
  if [ "${RET}" == "0" ]; then
    ifconfig ${IF_NAME} up
    logger -s "The interface [${IF_NAME}] is up!"
    if [ ! -e "/sys/bus/usb-serial/drivers/pl2303/ttyUSB1" ]; then
      for m in ${MODULE_IDS}
      do
        echo "${m/:/ }" > /sys/bus/usb-serial/drivers/pl2303/new_id
      done
    fi
  else
    IF_NAME=""
  fi
}

# start banner
logger -s "Initializing CANDY IoT Board..."

diagnose_self
activate_lte

# end banner
logger -s "CANDY IoT Board is initialized successfully!"

/usr/bin/env python /opt/robotma/candy-iot/server_main.py /dev/ttyUSB1 /var/run/candy-iot.sock ${IF_NAME}
