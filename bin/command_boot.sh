source ~/.bash_profile

echo "[$(date +'%Y-%m-%d %H:%M:%S')] command_start.sh"
 
conda activate premium

PID=$(ps -ef | grep commandMain.py | grep -v grep | awk {'print $2'})

# PID 값이존재하지 않을 때
if [ -z $PID ]
then
        echo "Start commandMain.py"

        sleep 1
        nohup python3 /root/arbitrage/commandMain.py > /dev/null 2>&1 &

        sleep 1
        ps -ef | grep commandMain.py | grep -v grep
else
        echo "commandMain.py is running"
fi

