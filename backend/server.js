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
    
    // 去 crew_members 表里找账号密码
    const sql = 'SELECT * FROM crew_members WHERE username = ? AND password = ?';
    db.query(sql, [username, password], (err, results) => {
        if (err) return res.status(500).json({ success: false, message: '服务器内部错误' });
        
        if (results.length > 0) {
            const user = results[0];
            // 登录成功，告诉前端这个人是 admin 还是 user
            res.json({ 
                success: true, 
                message: '登录成功', 
                role: user.role, 
                name: user.name 
            });
        } else {
            // 查不到数据，说明密码错了
            res.status(401).json({ success: false, message: '账号或密码错误' });
        }
    });
});

// 3. 启动服务器，监听 3000 端口
app.listen(3000, () => {
    console.log('🚀 后端服务器已启动，正在监听端口 3000');
});