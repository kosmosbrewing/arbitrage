source ~/.bash_profile

echo "[$(date +'%Y-%m-%d %H:%M:%S')] make_graph.sh"

conda activate premium

sleep 3 

export PYTHONPATH=/root/arbitrage:$PYTHONPATH

python3 /root/arbitrage/graph/graph.py $1
