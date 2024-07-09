source ~/.bash_profile

echo "[$(date +'%Y-%m-%d %H:%M:%S')] boot_all.sh"

conda activate premium

PID=$(ps -ef | grep main.py | grep arbi | grep -v grep | awk {'print $2'})

# PID 값이존재하지 않을 때
if [ -z $PID ]
then
        echo "Boot main.py"

	sleep 1 
	nohup python3 /root/arbitrage/main.py > /dev/null 2>&1 &
	
	sleep 1
        ps -ef | grep main.py | grep -v grep
else
        echo "main.py is running"
fi

sleep 1

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

PID=$(ps -ef | grep commandMain.py | grep -v grep | awk {'print $2'})

# PID 값이존재하지 않을 때
if [ -z $PID ]
then
        echo "Boot commandMain.py"

        sleep 1
        nohup python3 /root/arbitrage/commandMain.py > /dev/null 2>&1 &

        sleep 1
        ps -ef | grep commandMain.py | grep -v grep
else
        echo "commandMain.py is running"
fi

