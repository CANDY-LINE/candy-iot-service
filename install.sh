#!/usr/bin/env bash

VENDOR_HOME=/opt/candy-line

SERVICE_NAME=candy-iot
GITHUB_ID=CANDY-LINE/candy-iot-service
VERSION=2.1.0

SERVICE_HOME=${VENDOR_HOME}/${SERVICE_NAME}
SRC_DIR="${SRC_DIR:-/tmp/$(basename ${GITHUB_ID})-${VERSION}}"
CANDY_RED=${CANDY_RED:-1}
KERNEL="${KERNEL:-$(uname -r)}"
CONTAINER_MODE=0
if [ "${KERNEL}" != "$(uname -r)" ]; then
  CONTAINER_MODE=1
fi
WELCOME_FLOW_URL=https://git.io/v6en7

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

function setup {
  [ "${DEBUG}" ] || rm -fr ${SRC_DIR}
  if [ "${CP_DESTS}" != "" ]; then
    rm -f "${CP_DESTS}"
    touch "${CP_DESTS}"
  fi
}

function assert_root {
  if [[ $EUID -ne 0 ]]; then
     echo "This script must be run as root"
     exit 1
  fi
}

function uninstall_if_installed {
  if [ -f "${SERVICE_HOME}/environment" ]; then
    ${SERVICE_HOME}/uninstall.sh > /dev/null
    systemctl daemon-reload
    info "Existing version of candy-iot has been uninstalled"
  fi
}

function cpf {
  cp -f $1 $2
  if [ "$?" == "0" ] && [ -f "${CP_DESTS}" ]; then
    if [ -f "$2" ]; then
      echo "$2" >> "${CP_DESTS}"
    else
      case "$2" in
        */)
        DEST="$2"
        ;;
        *)
        DEST="$2/"
        ;;
      esac
      echo "${DEST}$(basename $1)" >> "${CP_DESTS}"
    fi
  fi
}

function download {
  if [ -d "${SRC_DIR}" ]; then
    return
  fi
  cd /tmp
  curl -L https://github.com/${GITHUB_ID}/archive/${VERSION}.tar.gz | tar zx
  if [ "$?" != "0" ]; then
    err "Make sure internet is available"
    exit 1
  fi
}

function install_cdc_ether {
  RET=`lsmod | grep cdc_ether`
  RET=$?
  if [ "${RET}" == "0" ]; then
    return
  fi
  download

  MOD_DIR=/lib/modules/${KERNEL}/kernel/drivers/net/usb/
  mkdir -p ${MOD_DIR}
  cpf ${SRC_DIR}/lib/${KERNEL}/cdc_ether.ko ${MOD_DIR}

  if [ "${CONTAINER_MODE}" == "0" ]; then
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
  fi

  echo "cdc_ether" > /etc/modules-load.d/cdc_ether.conf
  info "cdc_ether has been installed"
  REBOOT=1
}

function install_candy_board {
  RET=`which pip`
  RET=$?
  if [ "${RET}" != "0" ]; then
    curl -L https://bootstrap.pypa.io/get-pip.py | /usr/bin/env python
  fi

  pip install --upgrade candy-board-cli
  pip install --upgrade candy-board-amt
}

function install_candy_red {
  if [ "${CANDY_RED}" == "0" ]; then
    return
  fi
  info "Installing CANDY RED..."
  cd ~
  npm install -g npm@latest-2
  npm cache clean
  WELCOME_FLOW_URL=${WELCOME_FLOW_URL} npm install -g --unsafe-perm candy-red
  REBOOT=1
}

function install_service {
  RET=`systemctl | grep ${SERVICE_NAME}.service`
  RET=$?
  if [ "${RET}" == "0" ]; then
    return
  fi
  download

  LIB_SYSTEMD="$(dirname $(dirname $(which systemctl)))"
  if [ "${LIB_SYSTEMD}" == "/" ]; then
    LIB_SYSTEMD=""
  fi
  LIB_SYSTEMD="${LIB_SYSTEMD}/lib/systemd"

  mkdir -p ${SERVICE_HOME}
  cpf ${SRC_DIR}/systemd/boot-apn.json ${SERVICE_HOME}
  cpf ${SRC_DIR}/systemd/environment.txt ${SERVICE_HOME}/environment
  sed -i -e "s/%VERSION%/${VERSION//\//\\/}/g" ${SERVICE_HOME}/environment
  FILES=`ls ${SRC_DIR}/systemd/*.sh`
  FILES="${FILES} `ls ${SRC_DIR}/systemd/server_*.py`"
  for f in ${FILES}
  do
    cpf ${f} ${SERVICE_HOME}
  done

  cp -f ${SRC_DIR}/systemd/${SERVICE_NAME}.service.txt ${SRC_DIR}/systemd/${SERVICE_NAME}.service
  sed -i -e "s/%VERSION%/${VERSION//\//\\/}/g" ${SRC_DIR}/systemd/${SERVICE_NAME}.service

  cpf ${SRC_DIR}/systemd/${SERVICE_NAME}.service ${LIB_SYSTEMD}/system/
  systemctl enable ${SERVICE_NAME}

  cpf ${SRC_DIR}/uninstall.sh ${SERVICE_HOME}

  info "${SERVICE_NAME} service has been installed"
  REBOOT=1
}

function teardown {
  [ "${DEBUG}" ] || rm -fr ${SRC_DIR}
  if [ "${CONTAINER_MODE}" == "0" ] && [ "${REBOOT}" == "1" ]; then
    alert "*** Please reboot the system! (enter 'reboot') ***"
  fi
}

function package {
  rm -f $(basename ${GITHUB_ID})-${VERSION}.tgz
  # http://unix.stackexchange.com/a/9865
  COPYFILE_DISABLE=1 tar --exclude="./.*" -zcf $(basename ${GITHUB_ID})-${VERSION}.tgz *
}

# main
if [ "$1" == "pack" ]; then
  package
  exit 0
fi
assert_root
uninstall_if_installed
setup
install_candy_board
install_cdc_ether
install_candy_red
install_service
teardown
