drop view if exists top_chores;
drop view if exists top_chores_per_user;

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

--insert standard data
update meta set message='0.3' where key='appversion';
update meta set message='0.3' where key='dbversion';
insert into meta values ('actions_per_page','50');
