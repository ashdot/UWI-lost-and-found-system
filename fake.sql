-- 1. Remove old test data to ensure a clean start
DELETE FROM "User";

-- 2. Insert updated test users with the Scrypt hash for 'testing123'
-- Malik Grant (student)
INSERT INTO "User" ("userID", "firstName", "lastName", "email", "password", "role") 
VALUES (
    620159283, 
    'Malik', 
    'Grant', 
    'malik.grant@mymona.uwi.edu', 
    'scrypt:32768:8:1$dQVEfNkYrxVLDoRg$e510abc53fd00e284379b6d9d3a68a580d727b0098b0fd353e193a3312c4407cf8b2438c1881d0f1ef86ad983a224eb794ad585d79d45f63ebeaf25830e9ba1a', 
    'student'
);

INSERT INTO "User" ("userID", "firstName", "lastName", "email", "password", "role") 
VALUES (
    620164713, 
    'Ashle', 
    'Johnson', 
    'ashlerose101@gmail.com', 
    'scrypt:32768:8:1$dQVEfNkYrxVLDoRg$e510abc53fd00e284379b6d9d3a68a580d727b0098b0fd353e193a3312c4407cf8b2438c1881d0f1ef86ad983a224eb794ad585d79d45f63ebeaf25830e9ba1a', 
    'student'
);

-- Dr. Angela Chin (staff)
INSERT INTO "User" ("userID", "firstName", "lastName", "email", "password", "role") 
VALUES (
    451223344, 
    'Dr. Angela', 
    'Chin', 
    'angela.chin@uwi.edu', 
    'scrypt:32768:8:1$dQVEfNkYrxVLDoRg$e510abc53fd00e284379b6d9d3a68a580d727b0098b0fd353e193a3312c4407cf8b2438c1881d0f1ef86ad983a224eb794ad585d79d45f63ebeaf25830e9ba1a', 
    'staff'
);

-- Sasha-Kay Williams (admin)
INSERT INTO "User" ("userID", "firstName", "lastName", "email", "password", "role") 
VALUES (
    451002938, 
    'Sasha-Kay', 
    'Williams', 
    'sasha-kay.williams@uwi.edu', 
    'scrypt:32768:8:1$dQVEfNkYrxVLDoRg$e510abc53fd00e284379b6d9d3a68a580d727b0098b0fd353e193a3312c4407cf8b2438c1881d0f1ef86ad983a224eb794ad585d79d45f63ebeaf25830e9ba1a', 
    'admin'
);