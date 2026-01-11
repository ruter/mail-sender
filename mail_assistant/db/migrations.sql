-- contacts table
CREATE TABLE IF NOT EXISTS contacts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    email TEXT NOT NULL
);

-- cc_mappings table
CREATE TABLE IF NOT EXISTS cc_mappings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    owner_name TEXT NOT NULL,
    contact_id INTEGER NOT NULL,
    FOREIGN KEY (contact_id) REFERENCES contacts(id) ON DELETE CASCADE
);

-- send_logs table
CREATE TABLE IF NOT EXISTS send_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT,
    owner_name TEXT,
    status TEXT,
    error_message TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- smtp_config table
CREATE TABLE IF NOT EXISTS smtp_config (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    smtp_server TEXT NOT NULL,
    port INTEGER NOT NULL,
    sender_email TEXT NOT NULL,
    password TEXT NOT NULL
);

-- mail_template table
CREATE TABLE IF NOT EXISTS mail_template (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    body_template TEXT NOT NULL DEFAULT '@{owner} 这是{month}月的绩效数据结果，请查收。',
    signature TEXT NOT NULL DEFAULT ''
);
