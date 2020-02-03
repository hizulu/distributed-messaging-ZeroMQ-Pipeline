from DatabaseConnection import DatabaseConnection
import env


class AutoTrigger:

    def __init__(self):
        # self.dbName = "db_autotrigger"
        self.dbName = env.DB_NAME
        self.db = DatabaseConnection(
            env.DB_HOST, env.DB_UNAME, env.DB_PASSWORD, self.dbName)

    def getTables(self):
        query = """
            select * from information_schema.TABLES
            where TABLE_SCHEMA = '{}' and TABLE_NAME not like "tb_sync_%"
        """.format(self.dbName)

        return self.db.executeFetchAll(query)

    def getColums(self, tableName):
        query = """
            select COLUMN_NAME, COLUMN_TYPE, COLUMN_KEY from information_schema.COLUMNS
            where TABLE_SCHEMA = '{}' and TABLE_NAME = '{}'
        """

        return self.db.executeFetchAll(query.format(self.dbName, tableName))

    def generate(self):
        # createing after insert change log trigger
        print('Creating Changelog Trigger')
        createAfterInsertChangelogTrigger = """CREATE TRIGGER `after_insert_changelog` AFTER INSERT ON `tb_sync_changelog` FOR EACH ROW BEGIN DECLARE finished INTEGER DEFAULT 0;DECLARE id INTEGER(11);DECLARE curClient CURSOR FOR SELECT client_unique_id FROM tb_sync_client;DECLARE CONTINUE HANDLER FOR NOT FOUND SET finished = 1;OPEN curClient;getClient: LOOP FETCH curClient INTO id; IF finished = 1 THEN LEAVE getClient; END IF; INSERT INTO tb_sync_outbox(row_id, table_name, `query`, msg_type, `client_unique_id`, created_at, updated_at, `unix_timestamp`) VALUES(new.row_id, new.table, new.query, new.type, id, new.created_at, NOW(), new.unix_timestamp); END LOOP getClient;CLOSE curClient; END"""

        print(self.db.executeCommit(createAfterInsertChangelogTrigger))

        tables = self.getTables()
        # make trigger to every table
        for tb in tables:
            colums = self.getColums(tb['TABLE_NAME'])
            insertIntoQuery = "insert into {}(".format(tb['TABLE_NAME'])
            for col in colums:
                if(col['COLUMN_KEY' == 'PRI']):
                    continue
                insertIntoQuery += ''
                # tableTriggerQuery = """CREATE TRIGGER `after_insert_buku` AFTER INSERT ON `tb_buku` FOR EACH ROW BEGIN DECLARE qry TEXT; DECLARE tb VARCHAR(100);SET qry := CONCAT("insert into tb_buku(nama_buku, jenisbuku_id, isbn, created_at, updated_at) values(", "'", new.nama_buku, "', ", new.jenisbuku_id, ", '", new.isbn, "', '", new.created_at, "', '", new.updated_at, "')");SET tb := "tb_buku";INSERT INTO `tb_sync_changelog`(`query`, `table`, `type`, row_id, `unix_timestamp`) VALUES(qry, tb, 'INS', new.buku_id, UNIX_TIMESTAMP());END"""

    def addUnixTimestampColumnToEveryTable(self):
        table = self.getTables()
        print('----------------')
        print('ALTERing every table add timestamp column')
        for tb in table['data']:
            print("Altering: {}".format(tb['TABLE_NAME']))
            columns = self.getColums(tb['TABLE_NAME'])
            lastColumn = columns['data'][len(columns['data']) - 1]

            alterTableQuery = """
                alter table {} add unix_timestamp_sync timestamp default current_timestamp on update current_timestamp after {}
            """.format(tb['TABLE_NAME'], lastColumn['COLUMN_NAME'])
            if(self.db.executeCommit(alterTableQuery)):
                print('Success adding timestamp column to table: {}'.format(
                    tb['TABLE_NAME']))
            else:
                print('Failed adding timestamp column to table: {} with error'.format(
                    tb['TABLE_NAME'], self.db.getLastCommitError()['msg']))


autotrigger = AutoTrigger()
autotrigger.addUnixTimestampColumnToEveryTable()
