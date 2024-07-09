source ~/.bash_profile

echo "[$(date +'%Y-%m-%d %H:%M:%S')] collect_restart.sh"

conda activate premium

PID=$(ps -ef | grep collectMain.py | grep -v grep | awk {'print $2'})

# PID 값이 존재할 때
if [ -n $PID ]
then
        echo "Shutdown collectMain.py"
        kill -9 ${PID}
        ps -ef | grep collectMain.py | grep -v grep
else
        echo "collectMain.py is not running"
fi

sleep 5

PID=$(ps -ef | grep collectMain.py | grep -v grep | awk {'print $2'})

# PID 값이존재하지 않을 때
if [ -z $PID ]
then
        echo "Boot collectMain.py"

        sleep 1
        nohup python3 /root/arbitrage/collectMain.py > /dev/null 2>&1 &

        sleep 1
        ps -ef | grep collectMain.py | grep -v grep
else
        echo "collectMain.py is running"
fi

sleep 1

