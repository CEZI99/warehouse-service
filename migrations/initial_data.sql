-- Создание таблицы остатков на складах (без изменений)
CREATE TABLE IF NOT EXISTS warehouse_stocks (
    warehouse_id VARCHAR(36) NOT NULL,
    product_id VARCHAR(36) NOT NULL,
    quantity INTEGER NOT NULL CHECK (quantity >= 0),
    last_updated TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (warehouse_id, product_id)
);

-- Создание таблицы перемещений с обновленной структурой
CREATE TABLE IF NOT EXISTS movements (
    movement_id VARCHAR(36) NOT NULL,
    movement_type VARCHAR(10) NOT NULL CHECK (movement_type IN ('arrival', 'departure')),
    warehouse_id VARCHAR(36) NOT NULL,
    product_id VARCHAR(36) NOT NULL,
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    processed_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    source VARCHAR(10) NOT NULL,
    destination VARCHAR(50),
    related_warehouse_id VARCHAR(36) NULL,
    last_updated TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (movement_id, movement_type)  -- Составной первичный ключ
);

-- -- Создание индексов для улучшения производительности
-- CREATE INDEX IF NOT EXISTS idx_movement_id ON movements (movement_id);
-- CREATE INDEX IF NOT EXISTS idx_warehouse_product ON warehouse_stocks (warehouse_id, product_id);
-- CREATE INDEX IF NOT EXISTS idx_movement_warehouse ON movements (warehouse_id);
-- CREATE INDEX IF NOT EXISTS idx_movement_product ON movements (product_id);
-- CREATE INDEX IF NOT EXISTS idx_movement_timestamp ON movements (timestamp);

-- Начальные остатки на складах (без изменений)
INSERT INTO warehouse_stocks (warehouse_id, product_id, quantity, last_updated)
VALUES 
    ('c1d70455-7e14-11e9-812a-70106f431230', '4705204f-498f-4f96-b4ba-df17fb56bf55', 1000, '2025-01-01 10:00:00+00'),
    ('c1d70455-7e14-11e9-812a-70106f431230', '5893fb72-1a4f-4e96-b8d2-ef45ab67cd34', 500, '2025-01-01 10:00:00+00'),
    ('25718666-6af6-4281-b5a6-3016e36fa557', '4705204f-498f-4f96-b4ba-df17fb56bf55', 800, '2025-01-01 10:00:00+00'),
    ('25718666-6af6-4281-b5a6-3016e36fa557', '7890abcd-ef12-3456-7890-1234567890ab', 300, '2025-01-01 10:00:00+00')
ON CONFLICT (warehouse_id, product_id) DO NOTHING;