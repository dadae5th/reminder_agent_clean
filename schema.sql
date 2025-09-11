-- schema.sql
CREATE TABLE IF NOT EXISTS tasks (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  title TEXT NOT NULL,
  assignee_email TEXT,
  frequency TEXT CHECK(frequency IN ('daily','weekly','monthly')) NOT NULL,
  due_date TEXT,
  status TEXT CHECK(status IN ('pending','done')) DEFAULT 'pending',
  hmac_token TEXT UNIQUE,
  last_completed_at TEXT,
  updated_at TEXT
);
CREATE TABLE IF NOT EXISTS users (
  email TEXT PRIMARY KEY,
  name TEXT
);
