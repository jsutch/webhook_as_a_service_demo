"""
initialize demo users and auth tokens
"""
import sqlitedict
sqlitedict.PICKLE_PROTOCOL = 4 #try to overcome the HIGHEST PICKLE problem
from sqlitedict import SqliteDict

def create_all():
    tokensdb = SqliteDict('/var/www/webhook/app/tokens.db', autocommit=True)
    tokensdb['clientA_ba104cab58c17314'] = '48a44d17902e960b8070a5f59eb5e02f'
    tokensdb['clientB_555a79bdb472ead3'] = '7bb412f92c35a92923ccd178d45ff30c'
    tokensdb['66666666666668'] = 'd7811aa4852d7c021df3da133f8d3e11ad1e5c42d3ed0a1a'
    tokensdb['66666666666661'] = 'd7811aa4852d7c021df3da133f8d3e11ad1e5c42d3ed0a1a'
    tokensdb.commit()
    return True
