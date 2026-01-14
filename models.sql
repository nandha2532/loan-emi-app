-- Run this SQL once (Neon SQL editor or psql). Creates required tables.

CREATE TABLE persons (
    id SERIAL PRIMARY KEY,
    name TEXT UNIQUE NOT NULL
);

CREATE TABLE loans (
    loan_id SERIAL PRIMARY KEY,
    person_id INT REFERENCES persons(id),
    loan_date DATE,
    amount NUMERIC,
    tenure INT,
    interest NUMERIC,
    emi_start DATE,
    active BOOLEAN DEFAULT TRUE
);

CREATE TABLE emi_schedule (
    id SERIAL PRIMARY KEY,
    loan_id INT REFERENCES loans(loan_id),
    emi_date DATE,
    principal NUMERIC,
    interest NUMERIC,
    total NUMERIC,
    balance NUMERIC
);
