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
/*Table structure for table `tb_buku` */

DROP TABLE IF EXISTS `tb_buku`;

CREATE TABLE `tb_buku` (
  `buku_id` int(11) NOT NULL AUTO_INCREMENT,
  `nama_buku` varchar(100) DEFAULT NULL,
  `jenisbuku_id` int(11) DEFAULT NULL,
  `isbn` varchar(50) DEFAULT NULL,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `last_action_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`buku_id`)
) ENGINE=InnoDB AUTO_INCREMENT=2058 DEFAULT CHARSET=utf8;

/*Table structure for table `tb_sync_changelog` */

DROP TABLE IF EXISTS `tb_sync_changelog`;

CREATE TABLE `tb_sync_changelog` (
  `log_id` bigint(20) NOT NULL AUTO_INCREMENT,
  `row_id` int(1) DEFAULT NULL COMMENT 'primary key of the table',
  `table` varchar(100) DEFAULT NULL,
  `query` text,
  `type` varchar(5) DEFAULT NULL,
  `is_proceed` tinyint(4) DEFAULT '0',
  `occur_at` bigint(20) DEFAULT NULL,
  `first_time_occur_at` bigint(20) DEFAULT NULL COMMENT 'time the msg created for the first time',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`log_id`)
) ENGINE=InnoDB AUTO_INCREMENT=2055 DEFAULT CHARSET=utf8;

/*Table structure for table `tb_sync_client` */

DROP TABLE IF EXISTS `tb_sync_client`;

CREATE TABLE `tb_sync_client` (
  `client_id` int(11) NOT NULL AUTO_INCREMENT,
  `client_unique_id` int(11) DEFAULT NULL,
  `client_key` varchar(255) DEFAULT NULL,
  `client_iv` varchar(25) DEFAULT NULL,
  `client_ip` varchar(20) DEFAULT NULL,
  `client_port` int(11) DEFAULT NULL,
  PRIMARY KEY (`client_id`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8;

/*Table structure for table `tb_sync_errors` */

DROP TABLE IF EXISTS `tb_sync_errors`;

CREATE TABLE `tb_sync_errors` (
  `error_id` bigint(20) NOT NULL AUTO_INCREMENT,
  `error_msg` text,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`error_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

/*Table structure for table `tb_sync_inbox` */

DROP TABLE IF EXISTS `tb_sync_inbox`;

CREATE TABLE `tb_sync_inbox` (
  `inbox_id` bigint(20) NOT NULL AUTO_INCREMENT,
  `row_id` int(11) DEFAULT NULL,
  `table_name` varchar(255) DEFAULT NULL,
  `msg_type` enum('INS','UPD','DEL','ACK','PRI') DEFAULT NULL,
  `msg_id` int(11) DEFAULT NULL,
  `query` text,
  `client_unique_id` int(11) DEFAULT NULL,
  `master_status` tinyint(4) DEFAULT '0',
  `is_process` tinyint(4) DEFAULT '0',
  `result_primary_key` int(11) DEFAULT '0' COMMENT 'primary key after process the query, due to differential PK between host',
  `first_time_occur_at` bigint(20) DEFAULT NULL,
  `occur_at` bigint(20) DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  `updated_at` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`inbox_id`)
) ENGINE=InnoDB AUTO_INCREMENT=758 DEFAULT CHARSET=utf8;

/*Table structure for table `tb_sync_log` */

DROP TABLE IF EXISTS `tb_sync_log`;

CREATE TABLE `tb_sync_log` (
  `log_id` bigint(20) NOT NULL AUTO_INCREMENT,
  `log_function` varchar(255) DEFAULT NULL,
  `log_msg` text,
  PRIMARY KEY (`log_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

/*Table structure for table `tb_sync_master` */

DROP TABLE IF EXISTS `tb_sync_master`;

CREATE TABLE `tb_sync_master` (
  `master_id` int(11) NOT NULL AUTO_INCREMENT,
  `master_unique_id` int(11) DEFAULT NULL,
  `master_key` varchar(200) DEFAULT NULL,
  `master_ip` varchar(100) DEFAULT NULL,
  `master_port` int(11) DEFAULT NULL,
  PRIMARY KEY (`master_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

/*Table structure for table `tb_sync_outbox` */

DROP TABLE IF EXISTS `tb_sync_outbox`;

CREATE TABLE `tb_sync_outbox` (
  `outbox_id` bigint(20) NOT NULL AUTO_INCREMENT,
  `row_id` int(11) DEFAULT NULL COMMENT 'primary key of table in local',
  `table_name` varchar(255) DEFAULT NULL,
  `msg_type` varchar(5) DEFAULT NULL,
  `msg_id` int(11) DEFAULT NULL COMMENT 'outbox_id from local',
  `query` text,
  `client_unique_id` int(11) DEFAULT NULL COMMENT 'client_unique_id',
  `is_sent` tinyint(4) DEFAULT '0',
  `is_arrived` tinyint(4) DEFAULT '0',
  `is_error` tinyint(4) DEFAULT '0',
  `status` enum('waiting','sent','arrived','canceled','retry') DEFAULT 'waiting',
  `first_time_occur_at` bigint(20) DEFAULT NULL,
  `occur_at` bigint(20) DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  `updated_at` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`outbox_id`)
) ENGINE=InnoDB AUTO_INCREMENT=2662 DEFAULT CHARSET=utf8;

/*Table structure for table `tb_sync_setting` */

DROP TABLE IF EXISTS `tb_sync_setting`;

CREATE TABLE `tb_sync_setting` (
  `setting_id` int(11) NOT NULL AUTO_INCREMENT,
  `setting_name` varchar(255) DEFAULT NULL,
  `setting_value` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`setting_id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8;

/*Table structure for table `tb_sync_synchronization` */

DROP TABLE IF EXISTS `tb_sync_synchronization`;

CREATE TABLE `tb_sync_synchronization` (
  `sync_id` bigint(20) NOT NULL AUTO_INCREMENT,
  `query` text,
  `type` tinyint(4) DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`sync_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

/* Trigger structure for table `tb_buku` */

DELIMITER $$

/*!50003 DROP TRIGGER*//*!50032 IF EXISTS */ /*!50003 `after_insert_buku` */$$

/*!50003 CREATE */ /*!50017 DEFINER = 'rama'@'%' */ /*!50003 TRIGGER `after_insert_buku` AFTER INSERT ON `tb_buku` FOR EACH ROW BEGIN
	declare qry text;
	declare tb varchar(100);

	set qry := concat("insert into tb_buku(nama_buku, jenisbuku_id, isbn, created_at, updated_at, last_action_at) values(", "'", new.nama_buku, "',", new.jenisbuku_id, ",'", new.isbn, "','", new.created_at, "','", new.updated_at, "','", new.last_action_at, "')");
	set tb := "tb_buku";
	
	
	insert into `tb_sync_changelog`(`query`, `table`, `type`, row_id, occur_at, first_time_occur_at) values(qry, tb, 'INS', new.buku_id, unix_timestamp(), unix_timestamp(new.last_action_at));
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
		
		insert into tb_sync_outbox(row_id, table_name, `query`, msg_type, `client_unique_id`, created_at, updated_at, occur_at, first_time_occur_at)
		values(new.row_id, new.table, new.query, new.type, id, new.created_at, now(), new.occur_at, unix_timestamp(new.first_time_occur_at));
	end loop getClient;
	
	close curClient;
	
    END */$$


DELIMITER ;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;
