drop view if exists overview;

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
