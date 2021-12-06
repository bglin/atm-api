--  schema for account and transaction data --


drop table if exists accounts;

create table accounts (
    acct_id text primary key,
    pin text,
    balance real,
    api_key text,
    exp_date text
);

drop table if exists transactions;

create table transactions (
    transact_id integer primary key autoincrement,
    acct_id integer,
    action_type text,
    amount real,
    balance real,
    time_stamp text,
    foreign key(acct_id) references accounts(acct_id)
);

drop table if exists atm;

create table atm (
    balance real
);