from DatabaseConnection import DatabaseConnection
import string
import random


class Instalation:

    def __init__(self, dbhost, dbname, dbusername, dbpass):
        self.dbName = dbname
        # self.dbName = env.DB_NAME
        self.db = DatabaseConnection(
            dbhost, dbusername, dbpass, dbname)

    def setUniqueId(self, id):
        self.uniqueId = id
        self.ignoreColums = ['sync_token', 'last_action_at']

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

    def randomString(self, stringLength=16):
        letters = string.ascii_letters
        return ''.join(random.choice(letters) for i in range(stringLength))

    def _createAfterInsertTrigger(self, tablename, columns=[]):
        triggername = f"after_insert_{tablename}"
        print(f"Creating `{triggername}`", end="...")
        header = f"""CREATE TRIGGER `{triggername}` AFTER INSERT ON `{tablename}`
        FOR EACH ROW BEGIN
        """

        declaration = """
        DECLARE qry TEXT;
	    DECLARE tb VARCHAR(100);
        """

        colWoPk = [col['COLUMN_NAME']
                   for col in columns if col['COLUMN_KEY'] != "PRI"]
        # creating fields string
        fields = ""
        lencol = len(colWoPk)
        i = 1
        for item in colWoPk:
            fields += item
            if(i < lencol):
                fields += ','
            i += 1
        #
        # creating value string
        values = ""
        prefix = "\",\"\'\","
        firstColDivider = ",\"\',\","
        secondColDivider = ",\",\'\","
        middle = ",\"\',\'\","
        sufix = ",\"\')\""
        values += prefix
        i = 1
        for col in colWoPk:
            values += f"new.{col}"
            if (i == 1):
                values += firstColDivider
            elif(i == 2):
                values += secondColDivider
            elif(i < lencol):
                values += middle
            i += 1
        values += sufix
        pk = columns[0]['COLUMN_NAME']
        #

        body = f"""
        SET qry := CONCAT("insert into {tablename}({fields}) values({values});
        SET tb := "{tablename}";

        INSERT INTO `tb_sync_changelog`(`query`, `table`, `type`, row_id, occur_at, first_time_occur_at, sync_token) VALUES(qry, tb, 'INS', new.{pk}, UNIX_TIMESTAMP(now(3)), new.last_action_at, new.sync_token);

        """

        footer = "END;"
        # print(header + declaration + body + footer)
        inserted = self.db.executeCommit(header + declaration + body + footer)
        return inserted

    def _createBeforeInsertTrigger(self, tablename):
        # before insert digunakan untuk membuat token dan last action at
        # pada setiap table yang di sinkron
        triggername = f"before_insert_{tablename}"
        print(f"Creating `{triggername}`", end="...")
        header = f"""CREATE TRIGGER `{triggername}` BEFORE INSERT ON `{tablename}`
        FOR EACH ROW BEGIN
        """

        declaration = """
        DECLARE auto_id BIGINT DEFAULT 0;
        #DECLARE sync_id_temp BIGINT DEFAULT 0;
        """

        body = f"""
        SELECT IFNULL(MAX(log_id), 0)+1 INTO auto_id
        FROM tb_sync_changelog;

        #SELECT IFNULL(MAX(sync_id), 0)+1 INTO sync_id_temp
        #FROM {tablename};

        #SET new.sync_id = sync_id_temp;
        IF new.sync_token IS NULL THEN
            SET new.sync_token = CAST(CONCAT('{self.uniqueId}', auto_id) AS UNSIGNED);
            SET new.last_action_at = UNIX_TIMESTAMP(now(6));
        END IF;
        """

        footer = "END;"

        created = self.db.executeCommit(header + declaration + body + footer)
        return created

    def _createAfterDeleteTrigger(self, tablename, pk):
        # after delete
        triggername = f"after_delete_{tablename}"
        print(f"Creating `{triggername}`", end="...")
        header = f"""CREATE
            TRIGGER `{triggername}` BEFORE DELETE ON `{tablename}`
            FOR EACH ROW BEGIN
        """

        declaration = """
        DECLARE qry TEXT;
	    DECLARE tb VARCHAR(100);
        DECLARE time_at DOUBLE DEFAULT 0;
        """

        body = f"""
        SET qry := old.{pk};
        SET tb := "{tablename}";
        SET time_at := UNIX_TIMESTAMP(NOW(3));

        INSERT INTO `tb_sync_changelog`(`query`, `table`, `type`, row_id, occur_at, first_time_occur_at, sync_token)
        VALUES(qry, tb, 'DEL', old.{pk}, time_at, time_at, old.sync_token);
        """

        footer = "END;"

        created = self.db.executeCommit(header + declaration + body + footer)
        return created

    def _createAfterUpdateTrigger(self, tablename, columns):
        triggername = f"after_update_{tablename}"
        print(f"Creating `{triggername}`", end="...")
        header = f"""CREATE TRIGGER `{triggername}` AFTER UPDATE ON `{tablename}`
        FOR EACH ROW BEGIN
        """

        declaration = """
        DECLARE update_query TEXT;
        DECLARE tb VARCHAR(100);
        DECLARE front_update TINYINT DEFAULT 0;
        DECLARE update_count TINYINT DEFAULT 0;
        """

        col = [col['COLUMN_NAME']
               for col in columns if col['COLUMN_KEY'] != "PRI" and col['COLUMN_NAME'] not in self.ignoreColums]
        pk = columns[0]['COLUMN_NAME']

        body = f"""
        SET update_query := "update {tablename} set ";"""

        for c in col:
            body += f"""
                IF !(new.{c} <=> old.{c}) THEN
                    SET front_update = front_update + 1;
                    SET update_count = update_count + 1;
                    IF(front_update > 1) THEN
                        SET update_query = CONCAT(update_query, ",");
                    END IF;
                    SET update_query = CONCAT(update_query, '{c}=', "'", new.{c}, "'");
                END IF;
                """
        body += f"""
       
        SET tb := '{tablename}';

        IF update_count > 0 THEN
            SET update_query := CONCAT(update_query, ",last_action_at='", new.last_action_at, "',", "sync_token='", new.sync_token, "'");	
            SET update_query := CONCAT(update_query, " where {pk}=", new.{pk});
            INSERT INTO `tb_sync_changelog`(`query`, `table`, `type`, row_id, occur_at, first_time_occur_at, sync_token) VALUES(update_query, tb, 'UPD', new.{pk}, UNIX_TIMESTAMP(NOW(3)), new.last_action_at, new.sync_token);
        END IF;
        """

        footer = "END;"
        # print(header + declaration + body + footer)
        created = self.db.executeCommit(header + declaration + body + footer)
        if not created:
            print(self.db.getLastCommitError())
        return created

    def _createBeforeUpdateTrigger(self, tablename):
        triggername = f"before_update_{tablename}"
        print(f"Creating `{triggername}`", end="...")
        header = f"""CREATE TRIGGER `{triggername}` BEFORE UPDATE ON `{tablename}`
        FOR EACH ROW BEGIN
        """

        declaration = """
        DECLARE auto_id BIGINT DEFAULT 0;
        """

        body = f"""
        SELECT IFNULL(MAX(log_id), 0)+1 INTO auto_id
        FROM tb_sync_changelog;

        IF new.sync_token = old.sync_token THEN
            SET new.sync_token = CAST(CONCAT('{self.uniqueId}', auto_id) AS UNSIGNED);
            SET new.last_action_at = UNIX_TIMESTAMP(NOW(6));
        END IF;
        """

        footer = "END;"

        created = self.db.executeCommit(header + declaration + body + footer)
        return created

    def generateSyncTrigger(self):
        print('--------------')
        print("Generate sync trigger")
        # prosedur
        # 1. mengambil semua tabel dari information schema
        # 2. mengambil setiap kolom dari information schema untuk dimasukkan ke triiger
        # triiger yang dibuat adalah after insert, before insert, after delete
        tables = self.getTables()
        if (tables['execute_status']):
            for tb in tables['data']:
                columns = self.getColums(tb['TABLE_NAME'])
                print('OK') if self._createAfterInsertTrigger(
                    tb['TABLE_NAME'], columns['data']) else print("ERROR")
                print('OK') if self._createBeforeInsertTrigger(
                    tb['TABLE_NAME']) else print("ERROR")
                print('OK') if self._createAfterDeleteTrigger(
                    tb['TABLE_NAME'], columns['data'][0]['COLUMN_NAME']) else print("ERROR")
                print('OK') if self._createAfterUpdateTrigger(
                    tb['TABLE_NAME'], columns['data']) else print("ERROR")
                print('OK') if self._createBeforeUpdateTrigger(
                    tb['TABLE_NAME']) else print("ERROR")

    def dropAllTrigger(self):
        print('--------------')
        print("Cleaning all trigger...")
        sql = "show triggers"
        triggers = self.db.executeFetchAll(sql)
        if (triggers['execute_status']):
            for trigger in triggers['data']:
                print('Deleting trigger `{}`'.format(
                    trigger['Trigger']), end="...")
                delete = self._dropTriggerIfExist(trigger['Trigger'])
                print("OK") if delete else print("ERROR")

    def _dropTriggerIfExist(self, trigger_name):
        sql = 'drop trigger if exists {}'.format(trigger_name)
        return self.db.executeCommit(sql)

    def generateDefaultTrigger(self):
        # generating after insert changelog
        print('--------------')
        # creating triiger
        print('Creating default trigger `{}`...'.format(
            'after_insert_changelog'), end=" ")
        header = """
            CREATE TRIGGER `{}` AFTER INSERT ON `tb_sync_changelog` FOR EACH ROW BEGIN
        """.format('after_insert_changelog')
        declaration = """
            DECLARE finished INTEGER DEFAULT 0;
            DECLARE id INTEGER(11);
            DECLARE curClient CURSOR FOR
            SELECT client_unique_id FROM tb_sync_client where client_mode = 2;
           DECLARE CONTINUE HANDLER FOR NOT FOUND SET finished = 1;
        """
        body = """
            OPEN curClient;

            getClient: LOOP
                FETCH curClient INTO id;
                IF finished = 1 THEN
                    LEAVE getClient;
                END IF;

                INSERT INTO tb_sync_outbox(row_id, table_name, `query`, msg_type, `client_unique_id`, created_at, occur_at, first_time_occur_at, sync_token)
                VALUES(new.row_id, new.table, new.query, new.type, id, new.created_at,
                       new.occur_at, new.first_time_occur_at, new.sync_token);
            END LOOP getClient;

            CLOSE curClient;
        """
        footer = """
            END;
        """
        create = self.db.executeCommit(
            header + ' ' + declaration + ' ' + body + ' ' + footer)
        if (not create):
            print("ERROR")
        else:
            print('OK')

        print('Creating default trigger `{}`...'.format(
            'before_insert_outbox'), end=" ")
        header = """
            CREATE
            TRIGGER `before_insert_outbox` BEFORE INSERT ON `tb_sync_outbox` 
            FOR EACH ROW BEGIN
        """
        declaration = """
            DECLARE ip VARCHAR(100);
            DECLARE ports INT(11);
            DECLARE skey VARCHAR(16);
            DECLARE iv VARCHAR(16);
        """
        body = """
            IF (new.client_unique_id <> 0) THEN	
                SELECT client_ip, client_port, client_key, client_iv INTO ip, ports, skey, iv
                FROM tb_sync_client WHERE client_unique_id = new.client_unique_id;
                
                SET new.client_ip = ip;
                SET new.client_port = ports;
                SET new.client_key = skey;
                SET new.client_iv = iv;
            END IF;
        """
        footer = """
            END;
        """
        create = self.db.executeCommit(
            header + ' ' + declaration + ' ' + body + ' ' + footer)
        if (not create):
            print("ERROR")
        else:
            print('OK')

    def __createChanglogTable(self):
        sql = """
        CREATE TABLE `tb_sync_changelog` (
        `log_id` bigint(20) NOT NULL AUTO_INCREMENT,
        `row_id` int(1) DEFAULT NULL COMMENT 'primary key of the table',
        `table` varchar(100) DEFAULT NULL,
        `query` text,
        `type` varchar(5) DEFAULT NULL,
        `is_proceed` tinyint(4) DEFAULT '0',
        `first_time_occur_at` double DEFAULT NULL,
        `occur_at` double DEFAULT NULL,
        `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
        `sync_token` varchar(100) DEFAULT NULL,
        PRIMARY KEY (`log_id`)
        )
        """
        return self.db.executeCommit(sql)

    def __createClientTable(self):
        sql = """
            CREATE TABLE `tb_sync_client` (
            `client_id` int(11) NOT NULL AUTO_INCREMENT,
            `client_unique_id` int(11) DEFAULT NULL,
            `client_key` varchar(255) DEFAULT NULL,
            `client_iv` varchar(25) DEFAULT NULL,
            `client_ip` varchar(20) DEFAULT NULL,
            `client_port` int(11) DEFAULT NULL,
            `client_mode` tinyint(4) DEFAULT '2',
            PRIMARY KEY (`client_id`)
            )
        """
        return self.db.executeCommit(sql)

    def __createInboxTable(self):
        sql = """
        CREATE TABLE `tb_sync_inbox` (
        `inbox_id` bigint(20) NOT NULL AUTO_INCREMENT,
        `row_id` int(11) DEFAULT NULL,
        `table_name` varchar(255) DEFAULT NULL,
        `msg_type` enum('INS','UPD','DEL','ACK','PRI','REG','PROC','NEEDPK','DONE') CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL,
        `msg_id` int(11) DEFAULT NULL,
        `query` text,
        `client_unique_id` int(11) DEFAULT NULL,
        `master_status` tinyint(4) DEFAULT '0',
        `result_primary_key` int(11) DEFAULT '0' COMMENT 'primary key after process the query, due to differential PK between host',
        `status` enum('waiting','need_pk_update','done','error','processing') CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT 'waiting',
        `priority` tinyint(4) DEFAULT '2',
        `sync_token` varchar(100) DEFAULT NULL,
        `first_time_occur_at` double DEFAULT NULL,
        `occur_at` double DEFAULT NULL,
        `created_at` datetime DEFAULT NULL,
        `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (`inbox_id`)
        )
        """
        return self.db.executeCommit(sql)

    def __createOutboxTable(self):
        sql = """
        CREATE TABLE `tb_sync_outbox` (
        `outbox_id` bigint(20) NOT NULL AUTO_INCREMENT,
        `row_id` int(11) DEFAULT NULL COMMENT 'primary key of table in local',
        `table_name` varchar(255) DEFAULT NULL,
        `msg_type` enum('INS','UPD','DEL','ACK','PRI','REG','PROC','NEEDPK','DONE') CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL,
        `msg_id` int(11) DEFAULT NULL COMMENT 'outbox_id from local',
        `query` text,
        `client_unique_id` int(11) DEFAULT NULL COMMENT 'client_unique_id',
        `status` enum('waiting','sent','arrived','canceled','retry','need_pk_update','done','processing') CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT 'waiting',
        `priority` tinyint(4) DEFAULT '2',
        `sync_token` varchar(100) DEFAULT NULL,
        `retry_again_at` datetime DEFAULT NULL,
        `first_time_occur_at` double DEFAULT NULL,
        `occur_at` double DEFAULT NULL,
        `created_at` datetime DEFAULT NULL,
        `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
        `client_ip` varchar(100) DEFAULT NULL,
        `client_port` int(11) DEFAULT NULL,
        `client_key` varchar(16) DEFAULT NULL,
        `client_iv` varchar(16) DEFAULT NULL,
        PRIMARY KEY (`outbox_id`)
        )
        """
        return self.db.executeCommit(sql)

    def createSyncTable(self):
        print('--------------')
        print("Creating sync table")
        print('Creating changelog table', end="...")
        print('OK') if self.__createChanglogTable() else print('ERROR')
        print('Creating client table', end="...")
        print('OK') if self.__createClientTable() else print('ERROR')
        print('Creating inbox table', end="...")
        print('OK') if self.__createInboxTable() else print('ERROR')
        print('Creating outbox table', end="...")
        print('OK') if self.__createOutboxTable() else print('ERROR')

    def addUnixTimestampColumnToEveryTable(self):
        table = self.getTables()
        print('--------------')
        print('Adding sync column')
        for tb in table['data']:
            print(
                f"Add `last_action_at` column to `{tb['TABLE_NAME']}`", end="...")
            columns = self.getColums(tb['TABLE_NAME'])
            lastColumn = columns['data'][len(columns['data']) - 1]

            alterTableQuery = """
                alter table {} add last_action_at double after {}
            """.format(tb['TABLE_NAME'], lastColumn['COLUMN_NAME'])
            if(self.db.executeCommit(alterTableQuery)):
                print("OK")
            else:
                print('ERROR')

            print(
                f"Add `sync_token` column to `{tb['TABLE_NAME']}`", end="...")
            addSyncTokenQuery = f"alter table {tb['TABLE_NAME']} add sync_token varchar(100) after last_action_at"
            print('OK') if self.db.executeCommit(
                addSyncTokenQuery) else print("ERROR")

            # print(
            #     f"Add `sync_id` column to `{tb['TABLE_NAME']}`", end="...")
            # addSyncTokenQuery = f"alter table {tb['TABLE_NAME']} add sync_id int after sync_token"
            # print('OK') if self.db.executeCommit(
            #     addSyncTokenQuery) else print("ERROR")


# autotrigger = Instalation("localhost", "db_coba", 'rama', 'ramapradana24')
# autotrigger.dropAllTrigger()
# autotrigger.createSyncTable()
# autotrigger.generateDefaultTrigger()
# autotrigger.addUnixTimestampColumnToEveryTable()
# autotrigger.generateSyncTrigger()
