#!/usr/bin/env bash

# Copyright (c) 2015 Robotma.com

ROBOTMA_HOME=/opt/robotma

SERVICE_NAME=candy-iot
GITHUB_ID=Robotma-com/candy-iot-service

SERVICE_HOME=${ROBOTMA_HOME}/${SERVICE_NAME}

REBOOT=0

function err {
  echo -e "\033[91m[ERROR] $1\e[0m"
}

function info {
  echo -e "\033[92m[INFO] $1\e[0m"
}

function alert {
  echo -e "\033[93m[ALERT] $1\e[0m"
}

function uninstall_cdc_ether {
  RET=`lsmod | grep cdc_ether`
  RET=$?
  if [ "${RET}" != "0" ]; then
    return
  fi

  rmmod cdc_ether
  MOD_DIR=/lib/modules/$(uname -r)/kernel/drivers/net/usb/
  rm -f ${MOD_DIR}/cdc_ether.ko
  rm -f /etc/modules-load.d/cdc_ether.conf
  [ "$(ls -A ${MOD_DIR})" ] || rmdir ${MOD_DIR}
  info "cdc_ether has been uninstalled"
  REBOOT=1
}

function uninstall_service {
  RET=`systemctl | grep ${SERVICE_NAME}.service`
  RET=$?
  if [ "${RET}" == "0" ]; then
    systemctl stop ${SERVICE_NAME}
    systemctl disable ${SERVICE_NAME}
  fi
  
  LIB_SYSTEMD="$(dirname $(dirname $(which systemctl)))/lib/systemd"
  rm -f ${LIB_SYSTEMD}/system/${SERVICE_NAME}.service
  rm -f ${SERVICE_HOME}/environment
  rm -f ${SERVICE_HOME}/*.sh
  [ "$(ls -A ${SERVICE_HOME})" ] || rmdir ${SERVICE_HOME}
  info "${SERVICE_NAME} has been uninstalled"
  REBOOT=1
}

function teardown {
  if [ "${REBOOT}" == "1" ]; then
    alert "*** Please reboot the system! (enter 'reboot') ***"
  fi
}

# main
uninstall_service
uninstall_cdc_ether
teardown
