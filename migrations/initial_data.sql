-- Создание таблиц
CREATE TABLE IF NOT EXISTS warehouse_stocks (
    warehouse_id VARCHAR(36) NOT NULL,
    product_id VARCHAR(36) NOT NULL,
    quantity INTEGER NOT NULL CHECK (quantity >= 0),
    last_updated TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (warehouse_id, product_id)
);

CREATE TABLE IF NOT EXISTS movements (
    id VARCHAR(36) PRIMARY KEY,
    movement_id VARCHAR(36) NOT NULL,
    movement_type VARCHAR(20) NOT NULL CHECK (movement_type IN ('departure', 'arrival')),
    warehouse_id VARCHAR(36) NOT NULL,
    product_id VARCHAR(36) NOT NULL,
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    timestamp TIMESTAMP NOT NULL,
    processed_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    related_warehouse_id VARCHAR(36) NULL,
    source VARCHAR(10) NOT NULL,
    destination VARCHAR(50) NOT NULL,
    last_updated TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Начальные остатки на складах (соответствуют UUID формату из примеров)
INSERT INTO warehouse_stocks (warehouse_id, product_id, quantity, last_updated)
VALUES 
    ('c1d70455-7e14-11e9-812a-70106f431230', '4705204f-498f-4f96-b4ba-df17fb56bf55', 1000, '2025-01-01 10:00:00'),
    ('c1d70455-7e14-11e9-812a-70106f431230', '5893fb72-1a4f-4e96-b8d2-ef45ab67cd34', 500, '2025-01-01 10:00:00'),
    ('25718666-6af6-4281-b5a6-3016e36fa557', '4705204f-498f-4f96-b4ba-df17fb56bf55', 800, '2025-01-01 10:00:00'),
    ('25718666-6af6-4281-b5a6-3016e36fa557', '7890abcd-ef12-3456-7890-1234567890ab', 300, '2025-01-01 10:00:00')
ON CONFLICT (warehouse_id, product_id) DO NOTHING;

-- Примеры перемещений (адаптированные под ваши примеры сообщений)
INSERT INTO movements (
    id, 
    movement_id, 
    movement_type, 
    warehouse_id, 
    product_id, 
    quantity, 
    timestamp, 
    processed_at,
    related_warehouse_id,
    source,
    destination
)
VALUES
    -- Пара перемещений WH-3322 -> WH-3423
    (
        'b3b53031-e83a-4654-87f5-b6b6fb09fd99', 
        'c6290746-790e-43fa-8270-014dc90e02e0', 
        'departure', 
        '25718666-6af6-4281-b5a6-3016e36fa557', 
        '4705204f-498f-4f96-b4ba-df17fb56bf55', 
        100, 
        '2025-02-18T12:12:56Z'::timestamp, 
        '2025-02-18T12:13:00Z'::timestamp,
        'c1d70455-7e14-11e9-812a-70106f431230',
        'WH-3322',
        'ru.retail.warehouses'
    ),
    (
        'a1b2c3d4-e5f6-7890-1234-567890abcdef', 
        'c6290746-790e-43fa-8270-014dc90e02e0', 
        'arrival', 
        'c1d70455-7e14-11e9-812a-70106f431230', 
        '4705204f-498f-4f96-b4ba-df17fb56bf55', 
        100, 
        '2025-02-18T14:34:56Z'::timestamp, 
        '2025-02-18T14:35:00Z'::timestamp,
        '25718666-6af6-4281-b5a6-3016e36fa557',
        'WH-3423',
        'ru.retail.warehouses'
    ),
    -- Отдельное прибытие на WH-3423
    (
        'd4e5f6a7-b8c9-4d5e-6f7a-8b9c0d1e2f3a', 
        'f5a2c8d1-3e6b-4f9a-8c7d-654321fedcba', 
        'arrival', 
        'c1d70455-7e14-11e9-812a-70106f431230', 
        '5893fb72-1a4f-4e96-b8d2-ef45ab67cd34', 
        250, 
        '2025-01-20T09:15:30Z'::timestamp, 
        '2025-01-20T09:16:00Z'::timestamp,
        NULL,
        'WH-1150',
        'ru.retail.warehouses'
    );