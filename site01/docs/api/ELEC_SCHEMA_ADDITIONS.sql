-- ============================================
-- Electronics Database Schema Additions
-- Tables: ELEC_pnp, ELEC_pnp_data
-- Note: ELEC_board_files already exists for file storage
-- ============================================

-- Pick & Place Files
CREATE TABLE IF NOT EXISTS ELEC_pnp (
    id INT AUTO_INCREMENT PRIMARY KEY,
    board_id INT NOT NULL,
    filename VARCHAR(255) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    component_count INT DEFAULT 0,
    FOREIGN KEY (board_id) REFERENCES ELEC_boards(id) ON DELETE CASCADE,
    INDEX idx_board_id (board_id),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Pick & Place Component Data
CREATE TABLE IF NOT EXISTS ELEC_pnp_data (
    id INT AUTO_INCREMENT PRIMARY KEY,
    pnp_id INT NOT NULL,
    designator VARCHAR(50) NOT NULL,
    mid_x VARCHAR(20),
    mid_y VARCHAR(20),
    ref_x VARCHAR(20),
    ref_y VARCHAR(20),
    pad_x VARCHAR(20),
    pad_y VARCHAR(20),
    layer VARCHAR(10),
    rotation VARCHAR(10),
    comment VARCHAR(255),
    device VARCHAR(255),
    FOREIGN KEY (pnp_id) REFERENCES ELEC_pnp(id) ON DELETE CASCADE,
    INDEX idx_pnp_id (pnp_id),
    INDEX idx_designator (designator),
    INDEX idx_layer (layer)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- Sample Data (Optional)
-- ============================================

-- File type enum values (for reference, not enforced at DB level)
-- gerber, schematic, bom, pnp, datasheet, pcb_layout, ibom, documentation, firmware, cad

-- Layer values (for reference)
-- T, Top, B, Bottom
