from sqlitedict import SqliteDict
jobsdb = SqliteDict('jobs.db', autocommit=True)
tokensdb = SqliteDict('tokens.db', autocommit=True)
sessionsdb = SqliteDict('sessions.db', autocommit=True)
[(k, v) for k,v in tokensdb.items()]

