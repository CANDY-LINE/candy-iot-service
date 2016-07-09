#!/usr/bin/env bash

# Copyright (c) 2016 CANDY LINE, Inc.

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
function inactivate_lte {
  if [ "${MODULE_SUPPORTED}" != "1" ]; then
    return
  fi

  logger -s "Inactivating LTE/3G Module..."
  IF_NAME=`dmesg | grep "renamed network interface usb1" | sed 's/^.* usb1 to //g' | cut -f 1 -d ' '`
  RET=$?
  if [ "${RET}" == "0" ]; then
    ifconfig ${IF_NAME} down
    logger -s "The interface [${IF_NAME}] is down!"
    
    RET=`ifconfig | grep wlan0`
    RET=$?
    if [ "${RET}" == "0" ]; then
      ifconfig "wlan0" down
      ifconfig "wlan0" up
    fi
  fi
}

# start banner
logger -s "Inactivating CANDY IoT Board..."

diagnose_self
inactivate_lte

# end banner
logger -s "CANDY IoT Board is inactivated successfully!"
