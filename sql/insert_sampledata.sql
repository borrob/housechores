insert into roles values (-1,'none');
insert into roles values (2,'admin');
insert into roles values (3,'user');

insert into persons values (-1,'none','',-1);
insert into persons values (2,'admin','admin',2);
insert into persons values (3,'rob','rob',2);
insert into persons values (4,'random','asd',3);

insert into chores values (-1,'none');
insert into chores values (1,'dishes');
insert into chores values (2,'vacuum');
insert into chores values (3,'groceries jumbo');
insert into chores values (4,'groceries lidl');
insert into chores values (5,'change bedsheets');

insert into actions values (1,'2015-08-01',1,1);
insert into actions values (2,'2015-08-02',1,2);
insert into actions values (3,'2015-08-01',1,3);
insert into actions values (4,'2015-08-02',1,2);
insert into actions values (5,'2015-08-01',1,5);
insert into actions values (6,'2015-08-02',1,1);
