CREATE TABLE IF NOT EXISTS `ripple_tracking` (
  `user_id` int(11) NOT NULL DEFAULT '0',
  `username` text NOT NULL,
  `twitch_username` text,
  `mode` tinyint(4) NOT NULL DEFAULT '0',
  `stalk` tinyint(4) NOT NULL DEFAULT '0',
  `std_rank` int(11) NOT NULL DEFAULT '0',
  `std_pp` float NOT NULL DEFAULT '0',
  `taiko_rank` int(11) NOT NULL DEFAULT '0',
  `taiko_score` bigint(20) NOT NULL DEFAULT '0',
  `ctb_rank` int(11) NOT NULL DEFAULT '0',
  `ctb_score` bigint(20) NOT NULL DEFAULT '0',
  `mania_rank` bigint(20) NOT NULL DEFAULT '0',
  `mania_pp` float NOT NULL DEFAULT '0',
  PRIMARY KEY (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;