-- Datos de prueba iniciales para SISACAD
-- Correos generados con formato: apellido.nombre@unsa.edu.pe

-- Limpiar datos existentes
TRUNCATE TABLE estudiantes CASCADE;
TRUNCATE TABLE matriculas CASCADE;

-- Insertar estudiantes de ejemplo (basado en la imagen del Excel)
-- Todos inician en estado DESACTIVADO
INSERT INTO estudiantes (codigo, apellidos, nombres, correo_institucional, estado, fecha_creacion, fecha_actualizacion) VALUES
('20233590', 'ABENSUR ROMERO', 'DIEGO DANIEL', 'abensur.diego@unsa.edu.pe', 'DESACTIVADO', NOW(), NOW()),
('20232284', 'ALCAZAR MEDINA', 'DIOGO ANDRÃ‰', 'alcazar.diogo@unsa.edu.pe', 'DESACTIVADO', NOW(), NOW()),
('20230573', 'ALVA CORNEJO', 'JOSE JAVIER', 'alva.jose@unsa.edu.pe', 'DESACTIVADO', NOW(), NOW()),
('20213145', 'CACSIRE SANCHEZ', 'JHOSEP ANGEL', 'cacsire.jhosep@unsa.edu.pe', 'DESACTIVADO', NOW(), NOW()),
('20231537', 'CALCINA MUCHICA', 'SERGIO ELISEO', 'calcina.sergio@unsa.edu.pe', 'DESACTIVADO', NOW(), NOW()),
('20233598', 'CALIZAYA QUISPE', 'JOSE LUIS', 'calizaya.jose@unsa.edu.pe', 'DESACTIVADO', NOW(), NOW()),
('20222178', 'CAÃÂAPATA VARGAS', 'ALEX ENRIQUE', 'caÃ±apata.alex@unsa.edu.pe', 'DESACTIVADO', NOW(), NOW()),
('20222145', 'CARDENAS VILLAGOMEZ', 'PIERO ADRIANO', 'cardenas.piero@unsa.edu.pe', 'DESACTIVADO', NOW(), NOW()),
('20222179', 'CAYMA LMIR', 'JOSE RODRIGO', 'cayma.jose@unsa.edu.pe', 'DESACTIVADO', NOW(), NOW()),
('20233582', 'CASTELO CHOQUE', 'JOAQUIN ANDRÃ‰', 'castelo.joaquin@unsa.edu.pe', 'DESACTIVADO', NOW(), NOW()),
('20221737', 'CHAVEZ MEDINA', 'FERNANDO JESUS', 'chavez.fernando@unsa.edu.pe', 'DESACTIVADO', NOW(), NOW()),
('20230579', 'COLOMA VIURA', 'RIKI SANTHER', 'coloma.riki@unsa.edu.pe', 'DESACTIVADO', NOW(), NOW());

-- Insertar matrículas de ejemplo para el curso de Trabajo Interdisciplinar II
-- Las matrículas están en estado MATRICULADO
INSERT INTO matriculas (estudiante_codigo, curso_codigo, ciclo, grupo, orden, estado, fecha_matricula, fecha_actualizacion) VALUES
('20233590', 'TI-II', '2025-B', 'A', 1, 'MATRICULADO', NOW(), NOW()),
('20232284', 'TI-II', '2025-B', 'A', 2, 'MATRICULADO', NOW(), NOW()),
('20230573', 'TI-II', '2025-B', 'A', 3, 'MATRICULADO', NOW(), NOW()),
('20213145', 'TI-II', '2025-B', 'A', 4, 'MATRICULADO', NOW(), NOW()),
('20231537', 'TI-II', '2025-B', 'A', 5, 'MATRICULADO', NOW(), NOW()),
('20233598', 'TI-II', '2025-B', 'A', 6, 'MATRICULADO', NOW(), NOW()),
('20222178', 'TI-II', '2025-B', 'A', 7, 'MATRICULADO', NOW(), NOW()),
('20222145', 'TI-II', '2025-B', 'A', 8, 'MATRICULADO', NOW(), NOW()),
('20222179', 'TI-II', '2025-B', 'A', 9, 'MATRICULADO', NOW(), NOW()),
('20233582', 'TI-II', '2025-B', 'A', 10, 'MATRICULADO', NOW(), NOW()),
('20221737', 'TI-II', '2025-B', 'A', 11, 'MATRICULADO', NOW(), NOW()),
('20230579', 'TI-II', '2025-B', 'A', 12, 'MATRICULADO', NOW(), NOW());

-- Verificar los datos insertados
SELECT 
    codigo, 
    apellidos, 
    nombres, 
    correo_institucional, 
    estado 
FROM estudiantes
ORDER BY apellidos;

-- Contar por estado
SELECT estado, COUNT(*) as cantidad 
FROM estudiantes 
GROUP BY estado;

-- Verificar matrículas
SELECT COUNT(*) as total_matriculas FROM matriculas;
