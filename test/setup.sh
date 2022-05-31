set -e
echo "Creating mysql database... (Your mysql root user's password is needed)"
sudo mysql <<EOF
DROP USER IF EXISTS 'encrypted_mysqldb_user'@'localhost';
CREATE USER 'encrypted_mysqldb_user'@'localhost' IDENTIFIED BY 'encrypted_mysqldb_password';
CREATE DATABASE IF NOT EXISTS encrypted_mysqldb_test;
GRANT ALL PRIVILEGES ON encrypted_mysqldb_test.* TO 'encrypted_mysqldb_user'@'localhost';
FLUSH PRIVILEGES;
EOF
echo "Creating mysql database... DONE"
