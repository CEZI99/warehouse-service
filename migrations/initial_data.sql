-- Создание таблиц (если не созданы автоматически)
CREATE TABLE IF NOT EXISTS warehouse_stocks (
    warehouse_id VARCHAR(50) NOT NULL,
    product_id VARCHAR(50) NOT NULL,
    quantity INTEGER NOT NULL CHECK (quantity >= 0),
    last_updated TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (warehouse_id, product_id)
);

CREATE TABLE IF NOT EXISTS movements (
    id VARCHAR(50) PRIMARY KEY,
    movement_type VARCHAR(20) NOT NULL CHECK (movement_type IN ('departure', 'arrival')),
    warehouse_id VARCHAR(50) NOT NULL,
    product_id VARCHAR(50) NOT NULL,
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    timestamp TIMESTAMP NOT NULL,
    related_movement_id VARCHAR(50) NULL
);

-- Начальные остатки на складах
INSERT INTO warehouse_stocks (warehouse_id, product_id, quantity, last_updated)
VALUES 
    ('WH-001', 'PROD-001', 1000, '2025-01-01 10:00:00'),
    ('WH-001', 'PROD-002', 500, '2025-01-01 10:00:00'),
    ('WH-002', 'PROD-001', 800, '2025-01-01 10:00:00'),
    ('WH-002', 'PROD-003', 300, '2025-01-01 10:00:00')
ON CONFLICT (warehouse_id, product_id) DO NOTHING;

-- Примеры перемещений
INSERT INTO movements (id, movement_type, warehouse_id, product_id, quantity, timestamp, related_movement_id)
VALUES
    ('MOVE-001', 'departure', 'WH-001', 'PROD-001', 100, '2025-01-15 09:30:00', 'MOVE-002'),
    ('MOVE-002', 'arrival', 'WH-002', 'PROD-001', 100, '2025-01-15 14:15:00', 'MOVE-001'),
    ('MOVE-003', 'departure', 'WH-002', 'PROD-003', 50, '2025-01-16 11:20:00', NULL);