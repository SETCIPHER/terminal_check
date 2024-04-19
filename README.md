# <img src="https://github.com/SETCIPHER/terminal_check/blob/master/check.png" width="64" align="center"><figcaption> Terminal check</figcaption>
****Accessing the switch via a bot
This project shows the interaction of telnet requests in a telegram bot.<br />SNR, Huawei, BLM Ericsson switches have been tested.****

## Installation
For correct operation the following libraries must be installed:
``` {.bash}
pip3 install pyTelegramBotAPI
pip install mysql-connector-python
pip install pexpect
```
Create a passwd.py file in the project.
Specify access parameters
```{.bush}
TOKEN = "1234567890:QwErTyUiOp{aSdFgHjKl987654321"
ADMIN = [1234567890, 0987654321]t
LOGIN = 'tacaсs_login'
PASS = 'tacaсs_pass'
USER = 'admin'
SEC = 'pass'
```
Example to create a database in a file MySQL_config
