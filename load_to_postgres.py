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

with engine.connect() as conn:
    conn.execute(text("CREATE SCHEMA IF NOT EXISTS raw;"))
    conn.commit()
    print("Schema 'raw' has been prepared. ")

data_files = {
    "users_data.csv": "users",
    "products_data.csv": "products",
    "events_data.csv": "events",
    "orders_data.csv": "orders",
    "marketing_data.csv": "marketing"
}

for file_name, table_name in data_files.items():
    print("Loading data from '{}'".format(file_name))
    df = pd.read_csv(file_name)
    df.to_sql(name=table_name, con=engine, schema='raw', if_exists='replace', index=False)
    print("Loading data ended successfully")