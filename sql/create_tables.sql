--drop and create all the table for the sqlite db

--drop all the tables
drop view if exists overview;
drop view if exists chores_lastaction;
drop view if exists users;
drop view if exists xml_output;
drop view if exists xml_actions;
drop view if exists xml_persons;
drop view if exists xml_chores;
drop view if exists xml_roles;
drop view if exists top_chores;
drop view if exists top_chores_per_user;
drop table if exists actions;
drop table if exists persons;
drop table if exists chores;
drop table if exists roles;
drop table if exists meta;

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
		a.id,
		a.action_date,
		p.name as person_name,
		p.id as person_id,
		r.name as role,
		c.name as chore,
		c.id as chore_id
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

--chores last action
create view chores_lastaction as
	select
		c.id as chore_id,
		c.name as chore,
		max(a.action_date) as last_actioned
	from
		chores as c
	left join
		actions as a
	on
		c.id=a.chore_id
	group by
		c.id,
		c.name
	order by
		max(a.action_date) desc
;

--users
create view users as
	select
		p.id as person_id,
		p.name as person_name,
		r.id as role_id,
		r.name as role_name
	from
		persons as p
	left join
		roles as r
	on
		p.role_id=r.id
;

--xml
create view xml_roles as
	select '<roles>'
	union all
	select
		'    <id>' || id || '</id>' ||
		'    <name>' || name || '</name>'
	from
		roles
	union all
	select '</roles>'
;

create view xml_chores as
	select '<chores>' 
	union all
	select
		'    <id>' || id || '</id>' ||
		'    <name>' || name || '</name>'
	from
		chores
	union all
	select '</chores>'
;

create view xml_persons as
	select '<persons>'
	union all
	select
		'    <id>' || id || '</id>' ||
		'    <name>' || name || '</name>' ||
		'    <password>' || password || '</password>' ||
		'    <role_id' || role_id || '</role_id>'
	from
		persons
	union all
	select '</persons>'
;

create view xml_actions as
	select '<actions>'
	union all
	select
		'    <id>' || id || '</id>' ||
		'    <action_date>' || action_date || '</action_date>' ||
		'    <person_id>' || person_id || '</person_id>' ||
		'    <chore_id>' || chore_id || '</chore_id>'
	from
		actions
	union all
	select '</actions>'
;

create view xml_output as
	select * from xml_roles
	union all
	select ''
	union all
	select * from xml_chores
	union all
	select ''
	union all
	select * from xml_persons
	union all
	select ''
	union all
	select * from xml_actions
;

--top chores
create view top_chores as
	select
		c.name,
		count(*) as aantal
	from
		actions as a
	left join
		chores as c
	on
		a.chore_id=c.id
	group by
		c.name
	order by
		count(*) DESC
;

create view top_chores_per_user as
	select
		c.name,
		u.name as person,
		count(*) as aantal
	from
		actions as a
	left join
		chores as c
	on
		a.chore_id=c.id
	left join
		persons as u
	on
		a.person_id=u.id
	group by
		c.name,
		u.name
	order by
		count(*) desc
;

create table meta (
	key text,
	message text
);

--insert standard data
insert into roles values (1, 'admin');
insert into roles values (2,'user');
insert into persons (id, name, password, role_id) values (1,'admin', 'admin', 1);

insert into meta values ('appversion','0.4');
insert into meta values ('dbversion','0.4');
insert into meta values ('actions_per_page','50');
