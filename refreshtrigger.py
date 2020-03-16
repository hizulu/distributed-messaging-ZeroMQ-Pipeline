from instalation import Instalation
import env

print('Refreshing trigger...')
ins = Instalation(env.DB_HOST, env.DB_NAME, env.DB_UNAME, env.DB_PASSWORD)
ins.setUniqueId(env.UNIQUE_ID)
ins.dropAllTrigger()
ins.generateDefaultTrigger()
ins.generateSyncTrigger()
print("Finish")
