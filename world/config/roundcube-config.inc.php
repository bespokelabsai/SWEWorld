<?php
// Roundcube against maddy over plaintext IMAP on localhost. Closed world.
$config['db_dsnw'] = 'sqlite:////var/lib/world/roundcube/roundcube.db?mode=0646';
$config['imap_host'] = 'localhost:143';
$config['smtp_host'] = 'localhost:587';
$config['smtp_user'] = '%u';
$config['smtp_pass'] = '%p';
$config['support_url'] = '';
$config['product_name'] = 'SWEWorld Mail';
// Must be exactly 24 characters.
$config['des_key'] = 'sweworld-roundcube-des24';
$config['plugins'] = ['archive', 'zipdownload'];
$config['skin'] = 'elastic';
$config['temp_dir'] = '/var/lib/world/roundcube/temp';
$config['log_dir'] = '/var/lib/world/roundcube/logs';
$config['enable_installer'] = false;
$config['mail_domain'] = '%d';
