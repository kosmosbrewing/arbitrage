source ~/.bash_profile

echo "[$(date +'%Y-%m-%d %H:%M:%S')] command_restart.sh"

/root/arbitrage/bin/command_shutdown.sh

sleep 5

/root/arbitrage/bin/command_boot.sh
