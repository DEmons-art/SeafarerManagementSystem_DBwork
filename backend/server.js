const express = require('express');
const mysql = require('mysql2');
const cors = require('cors');

const app = express();
app.use(cors()); // 允许前端跨域访问
app.use(express.json()); // 解析前端传来的 JSON 数据

// 1. 连接 MySQL 数据库
const db = mysql.createConnection({
    host: '127.0.0.1',
    user: 'root',
    password: '123456', // 确认密码正确
    database: 'SeafarerDB' 
});

db.connect(err => {
    if (err) console.error('❌ 数据库连接失败:', err.message);
    else console.log('✅ MySQL 数据库连接成功！');
});

// ==========================================
// ====== 🔑 核心功能：系统登录接口 ======
// ==========================================
app.post('/api/login', (req, res) => {
    const { username, password } = req.body;
    const sql = 'SELECT * FROM crew_info WHERE username = ? AND password = ?';
    
    db.query(sql, [username, password], (err, results) => {
        if (err) return res.status(500).json({ success: false, message: '服务器错误' });
        
        if (results.length > 0) {
            const user = results[0];
            res.json({ 
                success: true, 
                message: '登录成功', 
                role: user.role, 
                name: user.name,
                id: user.id  // 💡 核心修复：把登录者的底层 ID 发给前端，用于后续权限隔离！
            });
        } else {
            res.status(401).json({ success: false, message: '账号或密码错误' });
        }
    });
});

// ==========================================
// ====== 👨‍💼 管理员端：船员管理与统计 ======
// ==========================================

// 获取所有船员
app.get('/api/crews', (req, res) => {
    const sql = 'SELECT id, username, password, name, gender, id_card, phone, is_at_sea, role FROM crew_info';
    db.query(sql, (err, results) => {
        if (err) return res.status(500).json({ success: false, message: '获取数据失败' });
        res.json({ success: true, data: results });
    });
});

// 新增船员
app.post('/api/crews', (req, res) => {
    const { username, password, name, gender, id_card, phone, role } = req.body;
    const sql = `INSERT INTO crew_info (username, password, name, gender, id_card, phone, is_at_sea, role) VALUES (?, ?, ?, ?, ?, ?, 0, ?)`;
    db.query(sql, [username, password, name, gender, id_card, phone, role], (err, results) => {
        if (err) {
            if (err.code === 'ER_DUP_ENTRY') return res.status(400).json({ success: false, message: '账号或身份证号已被注册！' });
            return res.status(500).json({ success: false, message: '写入失败' });
        }
        res.json({ success: true, message: '船员录入成功！' });
    });
});

// 删除船员
app.delete('/api/crews/:id', (req, res) => {
    const sql = 'DELETE FROM crew_info WHERE id = ?';
    db.query(sql, [req.params.id], (err, results) => {
        if (err) return res.status(500).json({ success: false, message: '删除失败' });
        res.json({ success: true, message: '船员已移出系统！' });
    });
});

// 切换出海状态
app.put('/api/crews/:id/status', (req, res) => {
    const sql = 'UPDATE crew_info SET is_at_sea = ? WHERE id = ?';
    db.query(sql, [req.body.is_at_sea, req.params.id], (err, results) => {
        if (err) return res.status(500).json({ success: false, message: '更新失败' });
        res.json({ success: true, message: '状态更新成功！' });
    });
});

// 获取统计数据看板
app.get('/api/stats', (req, res) => {
    const sql = 'SELECT COUNT(*) AS total_crew, SUM(is_at_sea) AS at_sea_count FROM crew_info';
    db.query(sql, (err, results) => {
        if (err) return res.status(500).json({ success: false });
        res.json({ success: true, data: { total: results[0].total_crew || 0, at_sea: results[0].at_sea_count || 0 } });
    });
});

// ==========================================
// ====== 🌊 管理员端：航次调度管理 ======
// ==========================================

// 获取所有航次（JOIN联表查询）
app.get('/api/voyages', (req, res) => {
    const sql = `
        SELECT v.*, c.name AS crew_name 
        FROM voyage_records v JOIN crew_info c ON v.crew_id = c.id
        ORDER BY v.record_id DESC
    `;
    db.query(sql, (err, results) => {
        if (err) return res.status(500).json({ success: false, message: '获取航次失败' });
        res.json({ success: true, data: results });
    });
});

// 分配新航次
app.post('/api/voyages', (req, res) => {
    const { crew_id, departure_point, destination_point, departure_time, expected_arrival_time } = req.body;
    const sql = `INSERT INTO voyage_records (crew_id, departure_point, destination_point, departure_time, expected_arrival_time, status) VALUES (?, ?, ?, ?, ?, '进行中')`;
    db.query(sql, [crew_id, departure_point, destination_point, departure_time, expected_arrival_time], (err, results) => {
        if (err) return res.status(500).json({ success: false, message: '分配失败' });
        res.json({ success: true, message: '航次任务分配成功！' });
    });
});

// ==========================================
// ====== 👤 船员用户端：个人专属接口 ======
// ==========================================

// 获取“我”的个人基本资料
app.get('/api/my-profile/:id', (req, res) => {
    const sql = 'SELECT id, username, name, gender, id_card, phone, is_at_sea FROM crew_info WHERE id = ?';
    db.query(sql, [req.params.id], (err, results) => {
        if (err || results.length === 0) return res.status(500).json({ success: false, message: '获取个人资料失败' });
        res.json({ success: true, data: results[0] });
    });
});

// 获取“我”的历史出海记录
app.get('/api/my-voyages/:id', (req, res) => {
    const sql = 'SELECT * FROM voyage_records WHERE crew_id = ? ORDER BY record_id DESC';
    db.query(sql, [req.params.id], (err, results) => {
        if (err) return res.status(500).json({ success: false, message: '获取航次记录失败' });
        res.json({ success: true, data: results });
    });
});

// 启动服务器
app.listen(3000, () => {
    console.log('🚀 后端服务器已启动，正在监听端口 3000');
});