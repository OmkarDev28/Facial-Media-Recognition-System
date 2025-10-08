create table event_participation(
	user_id INT,
	event_id INT, 
	foreign key (user_id) references users(id),
	foreign key (event_id) references events(id)
);