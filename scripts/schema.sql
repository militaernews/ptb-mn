CREATE TYPE file_type AS ENUM ('video', 'animation', 'photo');

drop table posts;

create table posts(
    post_id int primary key not null,
    media_group_id varchar(120),
    reply_id int,
    file_type int,
    file_id varchar(120)
)