-- Add designators column to ELEC_board_components table
-- Date: 2025-11-19

ALTER TABLE ELEC_board_components 
ADD COLUMN designators TEXT NULL 
COMMENT 'Comma-separated list of component designators (e.g., R1,R2,R3)';
