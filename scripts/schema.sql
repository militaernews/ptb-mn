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

-- Tracks posts that have already been forwarded to the suggest channel
-- to prevent duplicates and to support text-edit propagation.
create table if not exists suggest_posts
(
    source_channel_id  bigint       not null,
    source_message_id  int          not null,
    suggest_message_id int          not null,
    text               text,
    created_at         timestamptz  not null default now(),
    primary key (source_channel_id, source_message_id)
);

-- Whitelisted domains/links that are not to be deleted
create table if not exists whitelist
(
    id serial primary key,
    link text not null unique,
    created_at timestamptz not null default now()
);

-- User warnings
create table if not exists warnings
(
    user_id bigint not null,
    chat_id bigint not null,
    count int not null default 0,
    last_warned_at timestamptz not null default now(),
    primary key (user_id, chat_id)
);

-- User statistics for MNChat
create table if not exists user_stats
(
    user_id bigint not null,
    chat_id bigint not null,
    karma int not null default 0,
    message_count int not null default 0,
    joined_at timestamptz not null default now(),
    primary key (user_id, chat_id)
);
