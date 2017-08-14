use flasticles

DROP TABLE IF EXISTS users;

create table users(id INT(11) AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(100),
  email VARCHAR(100),
  username VARCHAR(30),
  password VARCHAR(100),
  register_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
