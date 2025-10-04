-- Enable the pgcrypto extension to generate UUIDs if it's not already enabled
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Create the users table only if it doesn't already exist
CREATE TABLE IF NOT EXISTS users (
    -- id: A unique identifier for the user (Primary Key)
    -- Using UUID for better security and scalability over auto-incrementing integers.
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- email: The user's email address.
    -- It must be unique and cannot be empty. Used for login.
    email VARCHAR(255) UNIQUE NOT NULL,

    -- hashed_password: The user's password after being securely hashed.
    -- We never store passwords in plain text for security reasons.
    hashed_password VARCHAR(255) NOT NULL,

    -- created_at: Timestamp of when the user account was created.
    -- Defaults to the current time.
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- updated_at: Timestamp of the last time the user's record was updated.
    -- Defaults to the current time.
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Optional: Create an index on the email column for faster login lookups.
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- Optional: Add a trigger to automatically update the updated_at timestamp
-- This function will be used by the trigger.
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
   NEW.updated_at = NOW();
   RETURN NEW;
END;
$$ language 'plpgsql';

-- Drop the trigger if it exists, to avoid errors on re-running the script
DROP TRIGGER IF EXISTS update_users_updated_at ON users;

-- Create the trigger that calls the function before any update on the users table.
CREATE TRIGGER update_users_updated_at
BEFORE UPDATE ON users
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

