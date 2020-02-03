/*
SQLyog Ultimate
MySQL - 8.0.12 : Database - db_ta
*********************************************************************
*/

/*!40101 SET NAMES utf8 */;

/*!40101 SET SQL_MODE=''*/;

/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;
/* Trigger structure for table `tb_buku` */

DELIMITER $$

/*!50003 DROP TRIGGER*//*!50032 IF EXISTS */ /*!50003 `after_insert_buku` */$$

/*!50003 CREATE */ /*!50017 DEFINER = 'rama'@'%' */ /*!50003 TRIGGER `after_insert_buku` AFTER INSERT ON `tb_buku` FOR EACH ROW BEGIN
	declare qry text;
	declare tb varchar(100);

	set qry := concat("insert into tb_buku(nama_buku, jenisbuku_id, isbn, created_at, updated_at) values(", "'", new.nama_buku, "',", new.jenisbuku_id, ",'", new.isbn, "','", new.created_at, "','", new.updated_at, "')");
	set tb := "tb_buku";
	
	
	insert into `tb_sync_changelog`(`query`, `table`, `type`, row_id, `unix_timestamp`) values(qry, tb, 'INS', new.buku_id, unix_timestamp());
    END */$$


DELIMITER ;

/* Trigger structure for table `tb_sync_changelog` */

DELIMITER $$

/*!50003 DROP TRIGGER*//*!50032 IF EXISTS */ /*!50003 `after_insert_changelog` */$$

/*!50003 CREATE */ /*!50017 DEFINER = 'rama'@'%' */ /*!50003 TRIGGER `after_insert_changelog` AFTER INSERT ON `tb_sync_changelog` FOR EACH ROW BEGIN
	
	declare finished integer default 0;
	declare id integer(11);
	
	declare curClient cursor for
		select client_unique_id from tb_sync_client;
	
	declare continue handler for not found set finished = 1;
	
	open curClient;
	
	getClient: loop
		fetch curClient into id;
		if finished = 1 then
			leave getClient;
		end if;
		
		insert into tb_sync_outbox(row_id, table_name, `query`, msg_type, `client_unique_id`, created_at, updated_at, `unix_timestamp`, unix_timestamp_sync)
		values(new.row_id, new.table, new.query, new.type, id, new.created_at, now(), new.unix_timestamp, unix_timestamp(new.unix_timestamp_sync));
	end loop getClient;
	
	close curClient;
	
    END */$$


DELIMITER ;

/* Procedure structure for procedure `generate_id` */

/*!50003 DROP PROCEDURE IF EXISTS  `generate_id` */;

DELIMITER $$

/*!50003 CREATE DEFINER=`rama`@`%` PROCEDURE `generate_id`(in table_name varchar(255))
BEGIN
		
		declare primary_key varchar(255);
		declare db_name varchar(255);
		declare max_id integer(11);
		
		#select db name and primary key of the table
		SELECT DATABASE() into db_name FROM DUAL; #db that currently active
		select COLUMN_NAME INTO primary_key from information_schema.`COLUMNS` 
		where information_schema.`COLUMNS`.`TABLE_SCHEMA` = db_name 
		and information_schema.`COLUMNS`.`TABLE_NAME` = table_name
		and information_schema.`COLUMNS`.`COLUMN_KEY` = 'PRI';
		
		set @query = concat('select max(', primary_key, ') into @max_id from ', table_name);
		
		prepare stmt from @query;
		execute stmt;
		DEALLOCATE PREPARE stmt;
		select @max_id;
		
		#select @query;
		#select primary_key;
		
	END */$$
DELIMITER ;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;
