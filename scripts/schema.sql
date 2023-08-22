drop table posts;

create table posts
(
    post_id        int,
    lang           char(2) not null,
    msg_id         int     not null,
    media_group_id varchar(120),
    reply_id       int,
    file_type      int,
    file_id        varchar(120),
    text           text,
    primary key (msg_id, lang)
);

create table promos
(
    user_id int not null,
    channel_id int,
    promo_id int,
    primary key (user_id)
);
