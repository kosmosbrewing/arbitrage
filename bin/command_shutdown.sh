source ~/.bash_profile

echo "[$(date +'%Y-%m-%d %H:%M:%S')] command_stop.sh"

PID=$(ps -ef | grep commandMain.py | grep -v grep | awk {'print $2'})

# PID 값이 존재할 때
if [ -n $PID ]
then
        echo "Stop commandMain.py"
        kill -9 ${PID}
        ps -ef | grep commandMain.py | grep -v grep
else
        echo "commandMain.py is not running"
fi



