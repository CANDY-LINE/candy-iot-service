#!/usr/bin/env bash

# Copyright (c) 2015 Robotma.com

ROBOTMA_HOME=/opt/robotma

SERVICE_NAME=candy-iot
GITHUB_ID=Robotma-com/candy-iot-service
VERSION=1.0.1

SERVICE_HOME=${ROBOTMA_HOME}/${SERVICE_NAME}
SRC_DIR=/tmp/candy-iot-service-${VERSION}

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

function setup {
  [ "${DEBUG}" ] || rm -fr ${SRC_DIR}
}

function download {
  if [ -d "${SRC_DIR}" ]; then
    return
  fi
  cd /tmp
  curl -L https://github.com/${GITHUB_ID}/archive/${VERSION}.tar.gz | tar zx
}

function install_cdc_ether {
  RET=`lsmod | grep cdc_ether`
  RET=$?
  if [ "${RET}" == "0" ]; then
    return
  fi
  download
  
  MOD_DIR=/lib/modules/$(uname -r)/kernel/drivers/net/usb/
  mkdir -p ${MOD_DIR}
  cp ${SRC_DIR}/lib/cdc_ether.ko ${MOD_DIR}
  depmod
  modprobe cdc_ether
  RET=$?
  if [ "${RET}" != "0" ]; then
    err "Failed to load cdc_ether!"
    rm -f ${MOD_DIR}/cdc_ether.ko
    rm -f /etc/modules-load.d/cdc_ether.conf
    teardown
    exit 1
  fi
  
  echo "cdc_ether" > /etc/modules-load.d/cdc_ether.conf
  info "cdc_ether has been installed"
  REBOOT=1
}

function install_service {
  RET=`systemctl | grep ${SERVICE_NAME}.service`
  RET=$?
  if [ "${RET}" == "0" ]; then
    return
  fi
  download
  
  LIB_SYSTEMD="$(dirname $(dirname $(which systemctl)))/lib/systemd"
  
  mkdir -p ${SERVICE_HOME}
  cp -f ${SRC_DIR}/systemd/environment ${SERVICE_HOME}
  cp -f ${SRC_DIR}/systemd/*.sh ${SERVICE_HOME}
  cp -f ${SRC_DIR}/systemd/${SERVICE_NAME}.service ${LIB_SYSTEMD}/system/
  cp -f ${SRC_DIR}/uninstall.sh ${SERVICE_HOME}
  systemctl enable ${SERVICE_NAME}
  info "${SERVICE_NAME} service has been installed"
  REBOOT=1
}

function teardown {
  [ "${DEBUG}" ] || rm -fr ${SRC_DIR}
  if [ "${REBOOT}" == "1" ]; then
    alert "*** Please reboot the system! (enter 'reboot') ***"
  fi
}

# main
setup
install_cdc_ether
install_service
teardown
