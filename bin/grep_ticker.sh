yesterday=$(date -d yesterday +%Y%m%d)

grep "Premium|" /root/arbitrage/log/premium.log > /root/arbitrage/log/premium_data.log_${yesterday}
