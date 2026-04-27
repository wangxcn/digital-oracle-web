# Digital Oracle Web

基于市场数据的预测分析 Web 服务。

## 快速启动

### 1. 安装依赖
```bash
cd digital-oracle-web
pip install -r requirements.txt
```

### 2. 启动服务
```bash
python main.py
```

### 3. 访问
- 前端: http://127.0.0.1:8080
- API: http://127.0.0.1:8080/api/analyze

## 部署到公网

### 方式1: 直接运行
```bash
python main.py
```
服务监听 0.0.0.0:8080，可通过 http://你的IP:8080 访问。

### 方式2: 使用 ngrok 内网穿透
```bash
# 安装 ngrok
ngrok http 8080
```

### 方式3: 使用 PM2 守护进程
```bash
pm2 start main.py --name digital-oracle
pm2 save
pm2 startup
```

## API 使用

### POST /api/analyze
```json
{
  "question": "WW3发生的概率是多少？"
}
```

### GET /api/health
返回服务状态。

## 功能

- Polymarket 预测市场数据
- 美债收益率曲线分析
- CNN Fear & Greed 情绪指数
- 加密货币行情
- 黄金/白银/原油价格
- 美联储利率预期
