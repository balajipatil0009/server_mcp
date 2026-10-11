"""Hand-written DDL matching the live MySQL schema.

`init_db()` is a no-op on an existing database (all statements are
`CREATE TABLE IF NOT EXISTS`) — it never drops or alters data.
"""
from app.core.database import conn_scope

DDL_STATEMENTS = (
    """CREATE TABLE IF NOT EXISTS `students` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `phone` varchar(15) NOT NULL,
  `standard` varchar(20) NOT NULL,
  `created_at` datetime NOT NULL DEFAULT (now()),
  `updated_at` datetime NOT NULL DEFAULT (now()),
  PRIMARY KEY (`id`),
  UNIQUE KEY `ix_students_phone` (`phone`),
  KEY `ix_students_name` (`name`),
  KEY `ix_students_standard` (`standard`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci""",
    """CREATE TABLE IF NOT EXISTS `marks` (
  `id` int NOT NULL AUTO_INCREMENT,
  `student_id` int NOT NULL,
  `subject` varchar(50) NOT NULL,
  `marks_obtained` float NOT NULL,
  `total_marks` float NOT NULL,
  `exam_type` varchar(30) NOT NULL,
  `term` varchar(20) NOT NULL,
  `exam_date` date DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT (now()),
  PRIMARY KEY (`id`),
  KEY `ix_marks_student_id` (`student_id`),
  KEY `ix_marks_subject` (`subject`),
  CONSTRAINT `marks_ibfk_1` FOREIGN KEY (`student_id`) REFERENCES `students` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci""",
    """CREATE TABLE IF NOT EXISTS `attendance` (
  `id` int NOT NULL AUTO_INCREMENT,
  `student_id` int NOT NULL,
  `date` date NOT NULL,
  `status` enum('present','absent','leave') NOT NULL,
  PRIMARY KEY (`id`),
  KEY `ix_attendance_date` (`date`),
  KEY `ix_attendance_student_id` (`student_id`),
  CONSTRAINT `attendance_ibfk_1` FOREIGN KEY (`student_id`) REFERENCES `students` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci""",
    """CREATE TABLE IF NOT EXISTS `behaviour` (
  `id` int NOT NULL AUTO_INCREMENT,
  `student_id` int NOT NULL,
  `score` int NOT NULL,
  `remark` text,
  `observed_by` varchar(100) DEFAULT NULL,
  `date` date DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT (now()),
  PRIMARY KEY (`id`),
  KEY `ix_behaviour_student_id` (`student_id`),
  CONSTRAINT `behaviour_ibfk_1` FOREIGN KEY (`student_id`) REFERENCES `students` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci""",
    """CREATE TABLE IF NOT EXISTS `curriculum_activities` (
  `id` int NOT NULL AUTO_INCREMENT,
  `student_id` int NOT NULL,
  `activity_name` varchar(100) NOT NULL,
  `category` enum('sports','arts','tech','academics_club','social','other') NOT NULL,
  `points` int NOT NULL,
  `achievement` varchar(150) DEFAULT NULL,
  `date` date DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `ix_curriculum_activities_student_id` (`student_id`),
  CONSTRAINT `curriculum_activities_ibfk_1` FOREIGN KEY (`student_id`) REFERENCES `students` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci""",
)


def init_db() -> None:
    """Create all tables if they do not exist yet."""
    with conn_scope() as conn:
        with conn.cursor() as cur:
            for stmt in DDL_STATEMENTS:
                cur.execute(stmt)
