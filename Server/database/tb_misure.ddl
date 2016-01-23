CREATE TABLE `tb_measures` (
  `timestamp` int(10) unsigned NOT NULL COMMENT 'Measure timestamp integer epoch time',
  `deploy_id` varchar(10) COLLATE latin1_general_ci NOT NULL COMMENT 'The universally unique name of this deployment',
  `node_id` smallint(6) NOT NULL COMMENT 'Sensor Node ID',
  `position` varchar(30) COLLATE latin1_general_ci DEFAULT NULL COMMENT 'Sensor location',
  `measure_name` varchar(10) COLLATE latin1_general_ci NOT NULL COMMENT 'The item measured',
  `unit` varchar(10) COLLATE latin1_general_ci DEFAULT NULL COMMENT 'unit of measure',
  `value` float NOT NULL COMMENT 'Measure value',
  PRIMARY KEY (`timestamp`,`deploy_id`,`node_id`,`measure_name`),
  KEY `THC_TIMESTAMP_IDX1` (`timestamp`),
  KEY `THC_IDX2` (`deploy_id`, `node_id`,`measure_name`),
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COLLATE=latin1_general_ci COMMENT='The main measure table';
