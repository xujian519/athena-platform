
from fastapi import FastAPI

app = FastAPI(title='平台监控', version='1.0.0')

@app.get('/')
async def root():
    return {'message': '平台监控服务运行正常', 'status': 'running'}

@app.get('/health')
async def health():
    return {'status': 'healthy', 'service': 'platform-monitor'}
