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
    udhcpc -i ${IF_NAME}
    logger -s "The interface [${IF_NAME}] is up!"
  fi
}

# start banner
logger -s "Initializing CANDY-IoT Board..."

diagnose_self
activate_lte

# end banner
logger -s "CANDY-IoT Board is initialized successfully!"
