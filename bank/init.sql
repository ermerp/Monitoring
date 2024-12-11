CREATE ROLE anon;

CREATE TABLE account
(
    id TEXT NOT NULL PRIMARY KEY,
    balance NUMERIC
);

GRANT USAGE ON SCHEMA public TO anon;
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE account TO anon;

CREATE OR REPLACE FUNCTION create_account(
    account_id TEXT,
    balance NUMERIC
) RETURNS BOOLEAN
    LANGUAGE plpgsql
AS
$$
BEGIN
    INSERT INTO account (id, balance)
    VALUES (account_id, balance);
    RETURN TRUE;
EXCEPTION
    WHEN OTHERS THEN
        RETURN FALSE;
END;
$$;

CREATE OR REPLACE FUNCTION delete_all_accounts() RETURNS BOOLEAN
    LANGUAGE plpgsql
AS $$
BEGIN
    DELETE FROM account;
    RETURN TRUE;
EXCEPTION
    WHEN OTHERS THEN
        RETURN FALSE;
END;
$$;

CREATE OR REPLACE FUNCTION transfer_balance(
    from_id TEXT,
    to_id TEXT,
    amount NUMERIC
) RETURNS BOOLEAN
    LANGUAGE plpgsql
AS $$
BEGIN
    IF from_id < to_id THEN
        -- Lock the row with the smaller id first
        PERFORM 1 FROM account WHERE id = from_id FOR UPDATE;
        PERFORM 1 FROM account WHERE id = to_id FOR UPDATE;
    ELSE
        -- Lock the row with the smaller id first
        PERFORM 1 FROM account WHERE id = to_id FOR UPDATE;
        PERFORM 1 FROM account WHERE id = from_id FOR UPDATE;
    END IF;

    -- Subtract amount from from_id
    UPDATE account
    SET balance = balance - amount
    WHERE id::TEXT = from_id;

    -- Add amount to to_id
    UPDATE account
    SET balance = balance + amount
    WHERE id::TEXT = to_id;

    RETURN TRUE;
EXCEPTION
    WHEN OTHERS THEN
        -- The transaction will be automatically rolled back
        RAISE;
        RETURN FALSE;
END;
$$;