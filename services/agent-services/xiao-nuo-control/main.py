import logging

from fastapi import FastAPI

app = FastAPI(title='小诺控制中心', version='1.0.0')

@app.get('/')
async def root():
    return {'message': '小诺控制中心运行正常', 'status': 'running'}

@app.get('/health')
async def health():
    return {'status': 'healthy', 'service': 'xiao-nuo-control'}
