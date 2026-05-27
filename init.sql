-- 0. 强制本次导入会话使用 utf8mb4 客户端字符集
-- 否则 docker mysql 入口脚本以 latin1 客户端导入本 UTF-8 文件，
-- 会把中文按 latin1 误读并二次编码，导致姓名/性别等出现“çŽ‹èˆ¹é•¿”式乱码。
SET NAMES utf8mb4;

-- 1. 船员基础信息表
CREATE TABLE IF NOT EXISTS crew_info (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '员工编号',
    username VARCHAR(50) UNIQUE COMMENT '登录账号',
    password VARCHAR(50) COMMENT '登录密码',
    name VARCHAR(50) NOT NULL COMMENT '姓名',
    gender ENUM('男', '女') DEFAULT '男',
    id_card VARCHAR(18) UNIQUE COMMENT '身份证号',
    phone VARCHAR(20) COMMENT '联系电话',
    is_at_sea TINYINT(1) DEFAULT 0 COMMENT '是否出海：0-在岸，1-出海中',
    role ENUM('user', 'admin') DEFAULT 'user' COMMENT '系统角色'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
-- 2. 出海行程记录表
CREATE TABLE IF NOT EXISTS voyage_records (
    record_id INT AUTO_INCREMENT PRIMARY KEY,
    crew_id INT NOT NULL COMMENT '关联船员ID',
    departure_point VARCHAR(100) NOT NULL COMMENT '出发港口',
    destination_point VARCHAR(100) NOT NULL COMMENT '目的港口',
    departure_time DATETIME COMMENT '出海时间',
    expected_arrival_time DATETIME COMMENT '预计到达时间',
    actual_arrival_time DATETIME DEFAULT NULL COMMENT '实际到达时间',
    status ENUM('进行中', '已抵达', '已取消') DEFAULT '进行中',
    FOREIGN KEY (crew_id) REFERENCES crew_info(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 3. 插入测试数据：一个管理员和一个普通船员
INSERT INTO crew_info (username, password, name, gender, id_card, phone, is_at_sea, role) VALUES 
('admin', 'admin123', '王船长', '男', '110101199001011234', '13800001111', 0, 'admin'),
('user01', '123456', '小李船员', '男', '110101199505055678', '13911112222', 1, 'user');
-- 4. 为小李添加一条“进行中”的出海记录
INSERT INTO voyage_records (crew_id, departure_point, destination_point, departure_time, expected_arrival_time, status) VALUES 
(2, '青岛港', '新加坡港', '2026-05-01 08:00:00', '2026-05-15 18:00:00', '进行中');
