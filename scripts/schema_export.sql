SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

CREATE TABLE public.persistence (
    data json NOT NULL
);

CREATE TABLE public.posts (
    post_id integer,
    lang character(2) NOT NULL,
    msg_id integer NOT NULL,
    media_group_id character varying(120),
    reply_id integer,
    file_type integer,
    file_id character varying(120),
    text text,
    spoiler boolean DEFAULT false NOT NULL
);

CREATE TABLE public.promos (
    user_id bigint NOT NULL,
    lang character(2),
    promo_id bigint
);

ALTER TABLE ONLY public.posts
    ADD CONSTRAINT posts_pkey PRIMARY KEY (msg_id, lang);

ALTER TABLE ONLY public.promos
    ADD CONSTRAINT promos_pkey PRIMARY KEY (user_id);