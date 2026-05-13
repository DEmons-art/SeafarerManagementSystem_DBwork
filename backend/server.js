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
    // ====== 新增 1：删除船员 (DELETE请求) ======
app.delete('/api/crews/:id', (req, res) => {
    // 从 URL 路径中抓取传过来的船员 ID (就像抓取数据包里的目的端口)
    const crewId = req.params.id; 
    
    const sql = 'DELETE FROM crew_info WHERE id = ?';
    db.query(sql, [crewId], (err, results) => {
        if (err) {
            console.error('删除失败:', err);
            return res.status(500).json({ success: false, message: '删除失败' });
        }
        res.json({ success: true, message: '船员已移出系统！' });
    });
});

// ====== 新增 2：一键切换出海状态 (PUT请求) ======
app.put('/api/crews/:id/status', (req, res) => {
    const crewId = req.params.id;
    // 接收前端发来的新状态：0代表在岸，1代表出海
    const { is_at_sea } = req.body; 
    
    const sql = 'UPDATE crew_info SET is_at_sea = ? WHERE id = ?';
    db.query(sql, [is_at_sea, crewId], (err, results) => {
        if (err) {
            console.error('状态更新失败:', err);
            return res.status(500).json({ success: false, message: '更新状态失败' });
        }
        res.json({ success: true, message: '状态更新成功！' });
    });
});

    
    // ====== 新增 3：获取统计数据接口 (GET请求) ======
app.get('/api/stats', (req, res) => {
    // 👨‍🏫 SQL新知识点：
    // COUNT(*) 就像是网工里的 IP 扫描，直接统计表里总共有多少行数据（多少人）。
    // SUM(is_at_sea) 是把所有人 is_at_sea 的值加起来。因为在岸是 0，出海是 1，加起来的总和正好就是出海的人数！
    const sql = 'SELECT COUNT(*) AS total_crew, SUM(is_at_sea) AS at_sea_count FROM crew_info';
    
    db.query(sql, (err, results) => {
        if (err) {
            console.error('统计失败:', err);
            return res.status(500).json({ success: false });
        }
        
        // 把查到的数据打包发给前端
        const data = {
            total: results[0].total_crew || 0,
            at_sea: results[0].at_sea_count || 0
        };
        res.json({ success: true, data: data });
    });
});


// ==========================================
// ====== 🌊 出海航次管理模块接口开始 🌊 ======
// ==========================================

// 1. 获取所有航次记录 (GET请求)
app.get('/api/voyages', (req, res) => {
    // 👨‍🏫 高分预警：这里使用了 SQL 的 JOIN（连表查询）！
    // 航次表里只有 crew_id (数字)，人看不懂。所以我们像查 ARP 缓存表一样，
    // 把 voyage_records(航次表) 和 crew_info(船员表) 通过 id 拼接在一起，
    // 直接把船员的真实姓名 (name) 查出来发给前端！
    const sql = `
        SELECT v.*, c.name AS crew_name 
        FROM voyage_records v
        JOIN crew_info c ON v.crew_id = c.id
        ORDER BY v.record_id DESC
    `;
    
    db.query(sql, (err, results) => {
        if (err) {
            console.error('获取航次列表失败:', err);
            return res.status(500).json({ success: false, message: '获取数据失败' });
        }
        res.json({ success: true, data: results });
    });
});

// 2. 分配全新航次 (POST请求)
app.post('/api/voyages', (req, res) => {
    // 从前端发来的数据包里提取：要派谁去(crew_id)、出发地、目的地、出发时间、预计到达时间
    const { crew_id, departure_point, destination_point, departure_time, expected_arrival_time } = req.body;
    
    // 插入数据库。注意：新分配的任务，状态默认直接就是 '进行中'
    const sql = `
        INSERT INTO voyage_records 
        (crew_id, departure_point, destination_point, departure_time, expected_arrival_time, status) 
        VALUES (?, ?, ?, ?, ?, '进行中')
    `;
    
    db.query(sql, [crew_id, departure_point, destination_point, departure_time, expected_arrival_time], (err, results) => {
        if (err) {
            console.error('🚨 新增航次写入失败:', err);
            // 防坑：如果前端传来的 crew_id 在船员表里根本不存在，MySQL的外键约束会报错拦截
            if (err.code === 'ER_NO_REFERENCED_ROW_2') {
                return res.status(400).json({ success: false, message: '分配失败：该船员不存在！' });
            }
            return res.status(500).json({ success: false, message: '服务器写入失败' });
        }
        res.json({ success: true, message: '🚢 航次任务分配成功！' });
    });
});

// ==========================================
// ====== 🌊 出海航次管理模块接口结束 🌊 ======



// 3. 启动服务器，监听 3000 端口
app.listen(3000, () => {
    console.log('🚀 后端服务器已启动，正在监听端口 3000');
});