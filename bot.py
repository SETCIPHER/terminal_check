#!/usr/bin/python
import telebot
import filters, passwd
import pexpect

from telebot import types
from search_base import search_user, search_login, search_id


bot = telebot.TeleBot(passwd.TOKEN)

users = passwd.ADMIN
@bot.message_handler(func=lambda message: message.chat.id not in users)
def access_msg(message):
 bot.send_message(message.chat.id, "Нет доступа! Обратитесь в группу СПД")

@bot.message_handler(commands=['search'])
def search(message):
  chat_id = message.chat.id
  msg = bot.send_message(chat_id, "Введите адрес:")
  bot.register_next_step_handler(msg, low_price_city_request)

def low_price_city_request(message):
   street_id = message.text
   result = search_user(street_id)
   keyboard = types.InlineKeyboardMarkup(row_width=1)
   
   if result:
     for row in result:
       
       button = types.InlineKeyboardButton(text=f"id {row[0]} MDU: {row[1]} {row[3]} {row[4]}", callback_data="lowprice_answer" +  str(row[0]))
       keyboard.add(button)
     mesg = bot.send_message(message.chat.id, "Результат поиска: " + street_id, reply_markup=keyboard)
     

keyboard = types.InlineKeyboardMarkup()
button1 = types.InlineKeyboardButton(text="route mac", callback_data="button1")
button2 = types.InlineKeyboardButton(text="dhcp", callback_data="button2")
button3 = types.InlineKeyboardButton(text="port", callback_data="button3")
button4 = types.InlineKeyboardButton(text="map", callback_data="button4")
keyboard.add(row_width=2).add(button1, button3)
keyboard.add(row_width=2).add(button2, button4)



# функция запустится, когда пользователь нажмет на кнопку
@bot.callback_query_handler(func=lambda call: True)
def answer(call):
    global address, login, mac, vlan, longtude, latitude
    if call.data.startswith("lowprice_answer"):
        msg = call.data.replace("lowprice_answer", '')

        id = msg
        result = search_id(id)
        if result:
         for row in result: 
            sent_message = bot.send_message(call.message.chat.id, f"id: {row[0]}  MDU: {row[1]}\nCity: {row[3]}\nAdress: {row[4]} {row[5]}\nModel: {row[2]}\nLogin: {row[7]} \nVlan: {row[8]} \nMac: {row[9]} \nIP: {row[10]}", reply_markup=keyboard)

            address = row[10] 
            mac = row[9]
            login = row[7]
            vlan = row[8]
            longtude = row[11] 
            latitude = row[12]

    if call.data == "button1":
        mesg = bot.send_message(call.from_user.id, 'Введите mac адрес роутера:  \n формат - aabb-ccdd-eeff')
        bot.register_next_step_handler(mesg, search_terminal)
    if call.data == "button2":
        mesg = bot.send_message(call.message.chat.id, 'Поиск активных сессии')
        return search_snooping(mesg)
    if call.data == "button3":
        mesg = bot.send_message(call.from_user.id, "Введите номер порта от 1 до 24:")
        bot.register_next_step_handler(mesg, search_terminal_port)
    if call.data == "button4":
        bot.send_location(call.from_user.id, longtude, latitude)
        

#==============PORT====================
def search_terminal_port(message):
  num_port = message.text
  chat_id = message.chat.id
  child = pexpect.spawn('telnet ' + address)
  index = child.expect(['login','Username','user: ', pexpect.EOF, pexpect.TIMEOUT])# ОТ 0 - login, 1- Username по причине разных коммутаторов 	

  try:
     match index: #  02.12.23
      case 0:
        child.sendline(passwd.LOGIN)
        child.expect('Password')
        child.sendline(passwd.PASS)
        child.expect('[#>]')
        child.sendline("show mac-address-table interface ethernet 1/0/" + num_port)
        child.sendline("show interface ethernet status | i 1/0/" + num_port)
        out = " "
        lst = filters.LIST_SNR + [vlan]
        patterns = ['#CLIENT#','--More--', pexpect.EOF] #перехват конца списка
        for ret in patterns:
           ret = child.expect(patterns)
           if ret == 0:
              out += child.before.decode('utf-8')
              break
           elif ret == 1:
               child.send(' ')
               out += child.before.decode('utf-8')
               continue
        for word in lst:
          out = out.replace(word, "")
        out = out.replace('\n', '').replace(login, '\nPort: ' + num_port).replace('1/0/' + num_port, '').replace('--','').replace(' -','')
        bot.send_message(chat_id,'Route mac: ' + out)
      case 1: # вынужден был продублировать из-за разных коммутаторов
        child.sendline(passwd.LOGIN)
        child.expect('Password')
        child.sendline(passwd.PASS)
        child.expect('[#>]')
        child.sendline("display mac-address dynamic Ethernet 0/0/" + num_port)
        out = ""
        lst = filters.LIST_HUAWEI + [vlan]
        patterns = ['<SOR','--More--', pexpect.EOF] #перехват конца списка
        for ret in patterns:
           ret = child.expect(patterns)
           if ret == 0:
              out += child.before.decode('utf-8')
              break
           elif ret == 1:
               child.send(' ')
               out += child.before.decode('utf-8')
               continue
        for word in lst:
         out = out.replace(word, "")
        out = out.replace('\n', '').replace('Ethernet 0/0/' + num_port,'\n Route mac: ')
        bot.send_message(chat_id, out)
        #bot.send_message(chat_id, out.splitlines()[4])
      case 2: # вынужден был продублировать из-за разных коммутаторов
        prompt = ["exit"]
        child.sendline(f'{passwd.USER}\r\n')
        child.expect('pass: ', timeout=5)
        child.sendline(f'{passwd.SEC}\r\n')
        child.expect([passwd.SR, passwd.UG])
        child.sendline(f'enable\r\n')
        lst_del = ['show ont ONID-'+mac +'-11-1.'+ num_port, mac] + filters.LIST_ERICSSON
        child.sendline(f'show ont ONID-{mac}-11-1.'+ num_port +' mib\r\n')
        child.sendline(f'show ont ONID-{mac}-11-1.'+ num_port +' bpmac\r\n')
        child.sendline(f'exit\r\n')
        child.expect(prompt, timeout=5)
        out = child.before.decode('utf-8')
        for word in lst_del:
         out = out.replace(word, '')
        out = out.replace('Administrative state', '\n Port state:').replace('Operational state', '\n Port link:').replace('Configuration indicator', '\n Link status:').replace('DISABLED', 'down').replace('ENABLED', 'up').replace('ONID11-1.', 'Port number: ').replace('-Port number: '+ num_port, '  Mac route:')

        bot.send_message(chat_id,f'`{login + num_port}`' + '\n' + out, parse_mode='Markdown')
        #print(out)
      case _:
         bot.send_message(chat_id, 'ошибка вышло время запроса')
  except Exception: bot.send_message(chat_id, 'запрос не сработал, нет данных!')
 # return search_ip(message)
  child.close()
#==============SEARCH MAC====================
def search_terminal(message):
  try:
     mac_id = message.text
     chat_id = message.chat.id
     child = pexpect.spawn('telnet ' + address)
     index = child.expect(['login', 'Username', pexpect.EOF, pexpect.TIMEOUT])# ОТ 0 - login, 1- Username по причине разных коммутаторов 
     child.sendline(passwd.LOGIN)
     pswd = child.expect('Password:')
     child.sendline(passwd.PASS)
     child.expect('[#>]')
     lst = ['address ' + mac_id, '-','     ']+ filters.LIST
     match index: #  02.12.23
      case 0:
        child.sendline("show mac-address-table address " + mac_id)
        out = ""
        patterns = ['#', '--More--', pexpect.EOF] #перехват конца списка
        for ret in patterns:
           ret = child.expect(patterns)
           if ret == 0:
              out += child.before.decode('utf-8')
              break
           elif ret == 1:
               child.send(' ')
               out += child.before.decode('utf-8')
               continue
        for word in lst:
         out = out.replace(word, "")
        bot.send_message(chat_id, out.rsplit('\n', 1)[0])
        #bot.send_message(chat_id, out.splitlines()[5])
      case 1: # вынужден был продублировать из-за разных коммутаторов
        child.sendline("display mac-address " + mac_id)
        out = ""
        patterns = ['<SOR','--More--', pexpect.EOF] #перехват конца списка
        for ret in patterns:
           ret = child.expect(patterns)
           if ret == 0:
              out += child.before.decode('utf-8')
              break
           elif ret == 1:
               child.send(' ')
               out += child.before.decode('utf-8')
               continue
        for word in lst:
         out = out.replace(word, "")
        bot.send_message(chat_id, out)
        #bot.send_message(chat_id, out.splitlines()[4])
      case _:
         bot.send_message(chat_id, 'ошибка вышло время запроса')
  except Exception: bot.send_message(chat_id, 'запрос не сработал, нет данных! \nНа Ericsson запрос не работает')
 # return search_ip(message)
  child.close()
	
	
#==============DHCP====================
def search_snooping(message):
  chat_id = message.chat.id
  
  try:
     child = pexpect.spawn('telnet ' + address)
     index = child.expect(['login','Username','user: ', pexpect.EOF, pexpect.TIMEOUT])# ОТ 0 - login, 1- Username по причине разных коммутаторов 
     lst = filters.LIST
     match index:
      case 0:
        child.sendline(passwd.LOGIN)
        pswd = child.expect('Password')
        child.sendline(passwd.PASS)
        child.expect('[#>]')
        child.sendline("show ip dhcp snooping binding all")
        out = ""
        patterns = ['#','--More--', pexpect.EOF] #перехват конца списка
        for ret in patterns:
           ret = child.expect(patterns)
           if ret == 0:
              out += child.before.decode('utf-8')
              break
           elif ret == 1:
               child.send(' ')
               out += child.before.decode('utf-8')
               continue
        for word in lst:
         out = out.replace(word, "")
        out = out.replace('nooping      count', " подключено  ")
        bot.send_message(chat_id, out.rsplit('\n', 1)[0])
      case 1: # 
        child.sendline(passwd.LOGIN)
        pswd = child.expect('Password')
        child.sendline(passwd.PASS)
        child.expect('[#>]')
        child.sendline("display dhcp snooping user-bind all")
        out = ""
        patterns = ['<SOR','--More--', pexpect.EOF] #перехват конца списка
        for ret in patterns:
           ret = child.expect(patterns)
           if ret == 0:
              out += child.before.decode('utf-8')
              break
           elif ret == 1:
               child.send(' ')
               out += child.before.decode('utf-8')
               continue
        for word in lst:
         out = out.replace(word, "")
        bot.send_message(chat_id, out.rsplit('\n', 1)[0])
        #bot.send_message(chat_id, out.splitlines()[8])
      case 2: # вынужден был продублировать из-за разных коммутаторов
        prompt = ["exit"]
        child.sendline(f'{passwd.USER}\r\n')
        child.expect('pass: ', timeout=5)
        child.sendline(f'{passwd.SEC}\r\n')
        child.expect([passwd.SR, passwd.UG])
        child.sendline(f'enable\r\n')
        lst_del = ['--','enable', passwd.DELSR , passwd.DELUG , 'show', 'ont-','ont','bpmac', 'ONT','UNI','OP', 'TYPE', 'AGE','MAC','FORWARD', 'DYNAMIC','660', mac] 
        child.sendline(f'show ont ont-{mac} bpmac\r\n')
        child.sendline(f'exit\r\n')
        child.expect(prompt, timeout=5)
        out = child.before.decode('utf-8')
        for word in lst_del:
         out = out.replace(word, '')
        bot.send_message(chat_id, out)
      case _:
         bot.send_message(chat_id, 'ошибка вышло время запроса')
  except Exception: bot.send_message(chat_id, 'запрос не сработал, нет данных')
 # return search_ip(message)
  child.close()
bot.polling()

