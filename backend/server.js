const express = require('express');
const mysql = require('mysql2');
const cors = require('cors');

const app = express();
app.use(cors()); // 允许前端跨域访问
app.use(express.json()); // 解析前端传来的 JSON 数据

// 1. 连接你的本地 MySQL 数据库
const db = mysql.createConnection({
    host: '127.0.0.1',
    user: 'root',
    password: '123456', // 👉 这里换成你的数据库密码
    database: 'SeafarerDB' // 👉 确认这是你在 Navicat 里建的数据库名
});

db.connect(err => {
    if (err) {
        console.error('❌ 数据库连接失败:', err.message);
    } else {
        console.log('✅ MySQL 数据库连接成功！');
    }
});

// 2. 写一个“登录”接口（网工作业核心考点：权限分离）
app.post('/api/login', (req, res) => {
    const { username, password } = req.body;
    
    const sql = 'SELECT * FROM crew_info WHERE username = ? AND password = ?';
    
    db.query(sql, [username, password], (err, results) => {
    
        if (err) {
            console.error('🚨 SQL报错详情:', err); // 👉 加了这一行，把真凶打印到黑窗口里
            return res.status(500).json({ success: false, message: '服务器错误' });
        }

        if (err) return res.status(500).json({ success: false, message: '服务器错误' });
        
        if (results.length > 0) {
            const user = results[0];
            res.json({ 
                success: true, 
                message: '登录成功', 
                role: user.role, 
                name: user.name 
            });
        } else {
            res.status(401).json({ success: false, message: '账号或密码错误' });
        }
    });

    app.get('/api/crews', (req, res) => {
        

    // 写 SQL 语句：去 crew_info 表里查数据，出于安全考虑，一般不把 password 查出来发给前端
    const sql = 'SELECT id, username, password,name, gender, id_card, phone, is_at_sea, role FROM crew_info';
    
    db.query(sql, (err, results) => {
        if (err) {
            console.error('查询船员失败:', err);
            return res.status(500).json({ success: false, message: '获取数据失败' });
        }
        // 把查到的结果打包发给前端
        res.json({ success: true, data: results });
    });
});

    // 获取所有出海航次记录 (GET 请求)
    app.get('/api/voyages', (req, res) => {
    const sql = `
        SELECT 
            v.record_id, 
            c.name AS crew_name, 
            v.departure_point, 
            v.destination_point, 
            v.departure_time, 
            v.expected_arrival_time, 
            v.status 
        FROM voyage_records v
        JOIN crew_info c ON v.crew_id = c.id
    `;
    
    db.query(sql, (err, results) => {
        if (err) {
            console.error('查询航次失败:', err);
            return res.status(500).json({ success: false, message: '获取数据失败' });
        }
        res.json({ success: true, data: results });
    });
});

});

    // ====== 新增：处理提交上来的船员数据 ======
app.post('/api/crews', (req, res) => {
    // 1. 从前端发来的请求体(req.body)里提取填写的表单数据
    const { username, password, name, gender, id_card, phone, role } = req.body;
    
    // 2. 准备 SQL 插入语句 (默认新入职的船员状态为 0-在岸)
    const sql = `INSERT INTO crew_info (username, password, name, gender, id_card, phone, is_at_sea, role) 
                 VALUES (?, ?, ?, ?, ?, ?, 0, ?)`;
                 
    // 3. 执行写入数据库
    db.query(sql, [username, password, name, gender, id_card, phone, role], (err, results) => {
        if (err) {
            console.error('🚨 新增船员失败:', err);
            // 💡 网工防坑细节：如果是账号或身份证重复，MySQL会报 ER_DUP_ENTRY 错误
            if (err.code === 'ER_DUP_ENTRY') {
                return res.status(400).json({ success: false, message: '添加失败：账号或身份证号已被注册！' });
            }
            return res.status(500).json({ success: false, message: '服务器写入失败' });
        }
        res.json({ success: true, message: '船员录入成功！' });
    });
});
// ==========================================

// 3. 启动服务器，监听 3000 端口
app.listen(3000, () => {
    console.log('🚀 后端服务器已启动，正在监听端口 3000');
});