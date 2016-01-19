CREATE TABLE `thc_misure` (
  `timestamp` int(10) unsigned NOT NULL COMMENT 'Il timestamp  della misura in intero epoch',
  `id_sensore` smallint(6) NOT NULL COMMENT 'l''ID del sensore',
  `posizione` varchar(30) COLLATE latin1_general_ci DEFAULT NULL COMMENT 'La posizione del sensore',
  `misura` varchar(10) COLLATE latin1_general_ci NOT NULL COMMENT 'la grandezza misurata (abbreviata)',
  `unita` varchar(10) COLLATE latin1_general_ci DEFAULT NULL COMMENT 'unità di misura',
  `valore` float NOT NULL COMMENT 'il valore della misura',
  PRIMARY KEY (`timestamp`,`id_sensore`,`misura`),
  KEY `THC_TIMESTAMP_IDX1` (`timestamp`),
  KEY `THC_IDX2` (`id_sensore`,`misura`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COLLATE=latin1_general_ci COMMENT='La tabella delle misure';
 
