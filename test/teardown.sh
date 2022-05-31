set -e
echo "Deleting mysql database... (Your mysql root user's password is needed)"
sudo mysql <<EOF
DROP DATABASE IF EXISTS encrypted_mysqldb_test;
DROP USER 'encrypted_mysqldb_user'@'localhost';
EOF
echo "Deleting mysql database... DONE"