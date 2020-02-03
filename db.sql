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
  `nama_buku` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL,
  `jenisbuku_id` int(11) DEFAULT NULL,
  `isbn` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `timestamp_sync` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`buku_id`)
) ENGINE=InnoDB AUTO_INCREMENT=2015 DEFAULT CHARSET=utf8;

/*Table structure for table `tb_sync_changelog` */

DROP TABLE IF EXISTS `tb_sync_changelog`;

CREATE TABLE `tb_sync_changelog` (
  `log_id` bigint(20) NOT NULL AUTO_INCREMENT,
  `row_id` int(1) DEFAULT NULL COMMENT 'primary key of the table',
  `table` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL,
  `query` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci,
  `type` varchar(5) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL,
  `is_proceed` tinyint(4) DEFAULT '0',
  `unix_timestamp` bigint(20) DEFAULT NULL,
  `unix_timestamp_sync` bigint(20) DEFAULT NULL COMMENT 'time the msg created for the first time',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`log_id`)
) ENGINE=InnoDB AUTO_INCREMENT=2015 DEFAULT CHARSET=utf8;

/*Table structure for table `tb_sync_client` */

DROP TABLE IF EXISTS `tb_sync_client`;

CREATE TABLE `tb_sync_client` (
  `client_id` int(11) NOT NULL AUTO_INCREMENT,
  `client_unique_id` int(11) DEFAULT NULL,
  `client_key` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL,
  `client_iv` varchar(25) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL,
  `client_ip` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL,
  `client_port` int(11) DEFAULT NULL,
  PRIMARY KEY (`client_id`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8;

/*Table structure for table `tb_sync_errors` */

DROP TABLE IF EXISTS `tb_sync_errors`;

CREATE TABLE `tb_sync_errors` (
  `error_id` bigint(20) NOT NULL AUTO_INCREMENT,
  `error_msg` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`error_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

/*Table structure for table `tb_sync_inbox` */

DROP TABLE IF EXISTS `tb_sync_inbox`;

CREATE TABLE `tb_sync_inbox` (
  `inbox_id` bigint(20) NOT NULL AUTO_INCREMENT,
  `row_id` int(11) DEFAULT NULL,
  `table_name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL,
  `msg_type` enum('INS','UPD','DEL','ACK','PRI') CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL,
  `msg_id` int(11) DEFAULT NULL,
  `query` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci,
  `client_unique_id` int(11) DEFAULT NULL,
  `master_status` tinyint(4) DEFAULT '0',
  `is_process` tinyint(4) DEFAULT '0',
  `result_primary_key` int(11) DEFAULT '0' COMMENT 'primary key after process the query, due to differential PK between host',
  `unix_timestamp` bigint(20) DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  `updated_at` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`inbox_id`)
) ENGINE=InnoDB AUTO_INCREMENT=736 DEFAULT CHARSET=utf8;

/*Table structure for table `tb_sync_log` */

DROP TABLE IF EXISTS `tb_sync_log`;

CREATE TABLE `tb_sync_log` (
  `log_id` bigint(20) NOT NULL AUTO_INCREMENT,
  `log_function` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL,
  `log_msg` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci,
  PRIMARY KEY (`log_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

/*Table structure for table `tb_sync_master` */

DROP TABLE IF EXISTS `tb_sync_master`;

CREATE TABLE `tb_sync_master` (
  `master_id` int(11) NOT NULL AUTO_INCREMENT,
  `master_unique_id` int(11) DEFAULT NULL,
  `master_key` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL,
  `master_ip` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL,
  `master_port` int(11) DEFAULT NULL,
  PRIMARY KEY (`master_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

/*Table structure for table `tb_sync_outbox` */

DROP TABLE IF EXISTS `tb_sync_outbox`;

CREATE TABLE `tb_sync_outbox` (
  `outbox_id` bigint(20) NOT NULL AUTO_INCREMENT,
  `row_id` int(11) DEFAULT NULL COMMENT 'primary key of table in local',
  `table_name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL,
  `msg_type` varchar(5) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL,
  `msg_id` int(11) DEFAULT NULL COMMENT 'outbox_id from local',
  `query` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci,
  `client_unique_id` int(11) DEFAULT NULL COMMENT 'client_unique_id',
  `is_sent` tinyint(4) DEFAULT '0',
  `is_arrived` tinyint(4) DEFAULT '0',
  `is_error` tinyint(4) DEFAULT '0',
  `status` enum('waiting','sent','arrived','canceled','retry') CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT 'waiting',
  `unix_timestamp_sync` bigint(20) DEFAULT NULL,
  `unix_timestamp` bigint(20) DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  `updated_at` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`outbox_id`)
) ENGINE=InnoDB AUTO_INCREMENT=2631 DEFAULT CHARSET=utf8;

/*Table structure for table `tb_sync_setting` */

DROP TABLE IF EXISTS `tb_sync_setting`;

CREATE TABLE `tb_sync_setting` (
  `setting_id` int(11) NOT NULL AUTO_INCREMENT,
  `setting_name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL,
  `setting_value` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL,
  PRIMARY KEY (`setting_id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8;

/*Table structure for table `tb_sync_synchronization` */

DROP TABLE IF EXISTS `tb_sync_synchronization`;

CREATE TABLE `tb_sync_synchronization` (
  `sync_id` bigint(20) NOT NULL AUTO_INCREMENT,
  `query` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci,
  `type` tinyint(4) DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`sync_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;
