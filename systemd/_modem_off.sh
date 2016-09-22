#!/usr/bin/env bash

echo -e "\033[93m[WARN] *** INTERNAL USE, DO NOT RUN DIRECTLY *** \033[0m"

function assert_root {
  if [[ $EUID -ne 0 ]]; then
     echo "This script must be run as root"
     exit 1
  fi
}

function cd_module_root {
  RET=`which realpath`
  RET=$?
  if [ "${RET}" == "0" ]; then
    REALPATH=`realpath "$0"`
  else
    REALPATH=`readlink -f -- "$0"`
  fi
  ROOT=`dirname ${REALPATH}`
  cd ${ROOT}
}

function exit_if_already_off {
  lsusb | grep 1ecb:0202 > /dev/null 2>&1
  if [ "$?" != "0" ]; then
    lsusb | grep 1ecb:0208 > /dev/null 2>&1
    if [ "$?" != "0" ]; then
      echo "OK (already OFF)"
      exit 0
    fi
  fi
}

function power_off {
  # Make POWER_KEY high to turn off module (toggle)
  echo 1 > ${POWER_KEY_PIN}/value
  sleep 3
  # Make POWER_KEY low after shutting down
  echo 0 > ${POWER_KEY_PIN}/value
}

function modem_off {
  . ${ROOT}/_pin_settings.sh > /dev/null 2>&1
  power_off
}

assert_root
cd_module_root
exit_if_already_off
modem_off
echo "OK"
