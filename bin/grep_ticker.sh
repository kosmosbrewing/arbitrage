date=$(date +%Y%m%d)

echo "[$(date +'%Y-%m-%d %H:%M:%S')] grep_ticker.sh"

grep "Premium|" /root/arbitrage/log/premium.log > /root/arbitrage/log/premium_data_${date}
