source ~/.bash_profile

echo "[$(date +'%Y-%m-%d %H:%M:%S')] restart.sh"

/root/arbitrage/bin/shutdown_all.sh

sleep 5

/root/arbitrage/bin/boot_all.sh
