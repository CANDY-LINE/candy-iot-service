#!/usr/bin/env bash

# Copyright (c) 2015 Robotma.com

MODULE_SUPPORTED=0

function diagnose_self {
  MODULE_IDS="1ecb:0208" # space delimiter

  RET=`dmesg | grep "register 'cdc_ether'"`
  RET=$?
  if [ "${RET}" != "0" ]; then
    return
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
    if [ ! -e "/sys/bus/usb-serial/drivers/pl2303/ttyUSB0" ]; then
      for m in ${MODULE_IDS}
      do
        echo "${m/:/ }" > /sys/bus/usb-serial/drivers/pl2303/new_id
      done
    fi
  else
    IF_NAME=""
  fi
}

function monitor_default_gw {
  if [ -z "${IF_NAME}" ]; then
    logger -s "The interface [${IF_NAME}] isn't ready. Shutting down."
    return
  fi

  while true
  do
    RET=`route | grep default | grep ${IF_NAME}`
    RET=$?
    if [ "${RET}" != "0" ]; then
      MYDHPC_PID=`ps | grep "udhcpc -i ${IF_NAME}" | grep -v "grep" | xargs | cut -f 1 -d ' '`
      if [ -n "${MYDHPC_PID}" ]; then
        kill -9 ${MYDHPC_PID}
      fi
      udhcpc -i ${IF_NAME}
    fi
    sleep 5
  done
}

# start banner
logger -s "Initializing CANDY-IoT Board..."

diagnose_self
activate_lte

# end banner
logger -s "CANDY-IoT Board is initialized successfully!"

monitor_default_gw
