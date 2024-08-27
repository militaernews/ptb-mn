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
    spoiler boolean default false,
    primary key (msg_id, lang)
);

drop table promos;

create table promos
(
    user_id bigint not null,
    lang char(2),
    promo_id bigint,
    primary key (user_id)
);
