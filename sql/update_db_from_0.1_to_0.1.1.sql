drop view if exists xml_output;
drop view if exists xml_actions;
drop view if exists xml_persons;
drop view if exists xml_chores;
drop view if exists xml_roles;

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
