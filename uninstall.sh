#!/usr/bin/env bash

VENDOR_HOME=/opt/candy-line

SERVICE_NAME=candy-iot
SERVICE_HOME=${VENDOR_HOME}/${SERVICE_NAME}

REBOOT=0

function err {
  echo -e "\033[91m[ERROR] $1\033[0m"
}

function info {
  echo -e "\033[92m[INFO] $1\033[0m"
}

function alert {
  echo -e "\033[93m[ALERT] $1\033[0m"
}

function assert_root {
  if [[ $EUID -ne 0 ]]; then
     echo "This script must be run as root"
     exit 1
  fi
}

function uninstall_candy_board {
  pip uninstall -y candy-board-amt
  pip uninstall -y candy-board-cli
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
  RET=`systemctl | grep ${SERVICE_NAME}.service | grep running`
  RET=$?
  if [ "${RET}" == "0" ]; then
    systemctl stop ${SERVICE_NAME}
  fi
  systemctl disable ${SERVICE_NAME}

  LIB_SYSTEMD="$(dirname $(dirname $(which systemctl)))/lib/systemd"
  rm -f ${LIB_SYSTEMD}/system/${SERVICE_NAME}.service
  rm -f ${SERVICE_HOME}/environment
  rm -f ${SERVICE_HOME}/*.sh
  rm -f ${SERVICE_HOME}/*.py
  rm -f ${SERVICE_HOME}/*.pyc
  rm -f ${SERVICE_HOME}/*.json
  systemctl daemon-reload
  info "${SERVICE_NAME} has been uninstalled"
  REBOOT=1
}

function teardown {
  [ "$(ls -A ${SERVICE_HOME})" ] || rmdir ${SERVICE_HOME}
  [ "$(ls -A ${VENDOR_HOME})" ] || rmdir ${VENDOR_HOME}
  if [ "${REBOOT}" == "1" ]; then
    alert "*** Please reboot the system! (enter 'reboot') ***"
  fi
}

# main
assert_root
uninstall_service
uninstall_candy_board
uninstall_cdc_ether
teardown
