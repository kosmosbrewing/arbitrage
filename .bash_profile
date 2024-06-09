# .bash_profile

# Get the aliases and functions
if [ -f ~/.bashrc ]; then
        . ~/.bashrc
fi

# User specific environment and startup programs
ARB_HOME=/root/arbitrage
PATH=$PATH:$HOME/bin:$ARB_HOME/bin
export PATH
set -o vi

alias vic='vi ~/.bash_profile'
alias so='source ~/.bash_profile'
alias vi='vim'
alias ah='cd $ARB_HOME'
alias alog='tail -f /root/arbitrage/log/premium.log'
alias log='tail -f /root/arbitrage/log/order.log'

export TERM=linux
export PS1="\[\e[36;1m\]\h@\[\e[32;1m\]\u:\[\e[31;1m\][\$PWD]\n\[\e[0m\]$ "
