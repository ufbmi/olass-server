
-- http://docs.sqlalchemy.org/en/latest/orm/extensions/automap.html
-- http://dev.mysql.com/doc/refman/5.7/en/sql-mode.html#sqlmode_allow_invalid_dates
-- SET SESSION sql_mode = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,ERROR_FOR_DIVISION_BY_ZERO,NO_AUTO_CREATE_USER,NO_ENGINE_SUBSTITUTION';

INSERT INTO version (version_id, version_info)
    VALUES('002', 'Create tables: partner, rule, linkage')
;


CREATE TABLE partner (
    partner_id integer unsigned NOT NULL AUTO_INCREMENT,
    partner_code char(5) NOT NULL,
    partner_description varchar(255) NOT NULL,
    partner_added_at datetime NOT NULL,
 PRIMARY KEY (partner_id),
 UNIQUE KEY (partner_code)
) ENGINE=InnoDB DEFAULT CHARSET=latin1
;

CREATE TABLE rule (
    rule_id integer unsigned NOT NULL AUTO_INCREMENT,
    rule_code char(5) NOT NULL,
    rule_description varchar(255) NOT NULL,
    rule_added_at datetime NOT NULL,
 PRIMARY KEY (rule_id),
 UNIQUE KEY (rule_code)
) ENGINE=InnoDB DEFAULT CHARSET=latin1
;

CREATE TABLE linkage (
    linkage_id bigint unsigned NOT NULL AUTO_INCREMENT,
    partner_id integer unsigned NOT NULL,
    rule_id integer unsigned NOT NULL,
    linkage_uuid char(36) NOT NULL,
    linkage_hash char(64) NOT NULL,
    linkage_added_at datetime NOT NULL,
 PRIMARY KEY (linkage_id),
 KEY (linkage_uuid),
 KEY (linkage_hash),
 KEY (linkage_added_at),
 CONSTRAINT `fk_linkage_partner_id` FOREIGN KEY (partner_id) REFERENCES partner (partner_id),
 CONSTRAINT `fk_linkage_rule_id` FOREIGN KEY (rule_id) REFERENCES rule (rule_id)
) ENGINE=InnoDB DEFAULT CHARSET=latin1
;

SHOW TABLES;
SELECT * FROM version;
