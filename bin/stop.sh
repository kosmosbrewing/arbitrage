source ~/.bash_profile

PID=$(ps -ef | grep main.py | grep -v grep | awk {'print $2'})

## PID 값이 존재할 때
if [ -n $PID ]
then
	echo "Stop main.py"
	kill -9 ${PID}
	ps -ef | grep main.py | grep -v grep
else
	echo "main.py is not running"
fi
