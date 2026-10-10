CREATE TABLE cooldowns (
    user_id TEXT NOT NULL,
    action_id TEXT NOT NULL,
    last_used INTEGER NOT NULL DEFAULT (unixepoch()),
    PRIMARY KEY (user_id, action_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);