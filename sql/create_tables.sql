--drop and create all the table for the sqlite db

--drop all the tables
drop view if exists overview;
drop table if exists actions;
drop table if exists persons;
drop table if exists chores;
drop table if exists roles;

--create new tables

--roles
create table roles (
	id integer primary key autoincrement,
	name text
);

--chores
create table chores (
	id integer primary key autoincrement,
	name text
);

--persons
create table persons (
	id integer primary key autoincrement,
	name text,
	password text, --for now just keeping the password as clear text
	role_id integer not null,
	foreign key(role_id) references roles(id)
);

--actions
create table actions (
	id integer primary key autoincrement,
	action_date integer,
	person_id integer not null,
	chore_id integer not null,
	foreign key(person_id) references persons(id),
	foreign key(chore_id) references chores(id)
);

--overview
create view overview as
	select
		a.action_date,
		p.name as person_name,
		r.name as role,
		c.name as chore
	from
		actions as a
	left join
		persons as p
	on
		a.person_id=p.id
	left join
		roles as r
	on
		p.role_id =r.id
	left join
		chores as c
	on
		a.chore_id=c.id
;
