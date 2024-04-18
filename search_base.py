import mysql.connector

db = mysql.connector.connect(
  host="localhost",
  user="user",
  password="qwerty1234",
  database="DataDB"
)
def search_user(street_id):
  cursor = db.cursor()
  query = "SELECT * FROM table_db WHERE street_id LIKE CONCAT('%', %s, '%')"
  values =(street_id,)
  cursor.execute(query, values)
  result = cursor.fetchall()
  return result
  pass

def search_login(login):
  cursor = db.cursor()
  query = "SELECT * FROM table_db WHERE login LIKE CONCAT('%', %s, '%')"
  values =(login,)
  cursor.execute(query, values)
  result = cursor.fetchall()
  return result
  pass

def search_id(id):
  cursor = db.cursor()
  query = "SELECT * FROM table_db WHERE id LIKE CONCAT(%s)"
  values =(id,)
  cursor.execute(query, values)
  result = cursor.fetchall()
  return result
  pass
