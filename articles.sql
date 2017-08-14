create table articles(id INT(11) AUTO_INCREMENT PRIMARY KEY,
  title VARCHAR(255),
   author VARCHAR(100),
   body TEXT,
   create_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP )
