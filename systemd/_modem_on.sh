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

function init_gpio {
  . ${ROOT}/_pin_settings.sh > /dev/null 2>&1
  setup_ports
  setup_pin_directions
}

function exit_if_already_on {
  lsusb | grep 1ecb:0202 > /dev/null 2>&1
  if [ "$?" == "0" ]; then
    echo "OK (already ON)"
    exit 0
  else
    lsusb | grep 1ecb:0208 > /dev/null 2>&1
    if [ "$?" == "0" ]; then
      echo "OK (already ON)"
      exit 0
    fi
  fi
}

function power_on {
  # Keep RESET_N high while inactive
  echo 1 > ${RESET_N_PIN}/value
  # Keep WWAN_DISABLE high while inactive (enable)
  echo 1 > ${WWAN_DISABLE_PIN}/value
  # Make POWER_KEY high to turn on module (toggle)
  echo 1 > ${POWER_KEY_PIN}/value
  sleep 2
  # Make POWER_KEY low after booting
  echo 0 > ${POWER_KEY_PIN}/value
}

function modem_on {
  power_on
}

assert_root
cd_module_root
init_gpio
exit_if_already_on
modem_on
echo "OK"
