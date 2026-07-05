import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy import text

USER = 'myuser'
PASSWORD = 'Password'
HOST = 'localhost'
PORT = '5432'
DB_NAME = 'smartreco_db'
DATABASE_URL = 'postgresql://{}:{}@{}:{}/{}'.format(USER, PASSWORD, HOST, PORT, DB_NAME)

engine = create_engine(DATABASE_URL)

query="SELECT * FROM raw.users LIMIT 5;"
df = pd.read_sql_query(query, engine)
print(df)