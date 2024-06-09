source ~/.bash_profile

echo "[$(date +'%Y-%m-%d %H:%M:%S')] shutdown_all.sh"

PID=$(ps -ef | grep main.py | grep arbi | grep -v grep | awk {'print $2'})

## PID 값이 존재할 때
if [ -n $PID ]
then
	echo "Shutdown main.py"
	kill -9 ${PID}
	ps -ef | grep main.py | grep -v grep
else
	echo "main.py is not running"
fi

sleep 1

PID=$(ps -ef | grep collectMain.py | grep -v grep | awk {'print $2'})

## PID 값이 존재할 때
if [ -n $PID ]
then
        echo "Shutdown collectMain.py"
        kill -9 ${PID}
        ps -ef | grep collectMain.py | grep -v grep
else
        echo "collectMain.py is not running"
fi

sleep 1

PID=$(ps -ef | grep commandMain.py | grep -v grep | awk {'print $2'})

## PID 값이 존재할 때
if [ -n $PID ]
then
        echo "Shutdown commandMain.py"
        kill -9 ${PID}
        ps -ef | grep commandMain.py | grep -v grep
else
        echo "commandMain.py is not running"
fi



