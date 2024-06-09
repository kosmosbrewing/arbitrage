#!/bin/bash
source ~/.bash_profile

echo "[$(date +'%Y-%m-%d %H:%M:%S')] main_restart.sh"

/root/arbitrage/bin/main_shutdown.sh

sleep 5

/root/arbitrage/bin/main_boot.sh
