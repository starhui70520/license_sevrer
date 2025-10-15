import models
import mana
from fastapi import FastAPI, HTTPException
import db
import configparser
from uvicorn import Config, Server
import asyncio
from db import db
from typing import Optional
from logger import get_logger

app = FastAPI(title="AgentBox许可证注册服务", version="0.1.0")

@app.get("/", tags=["Root"], summary="返回服务介绍")
async def read_root():
    """
    根路径，返回欢迎信息。
    """
    return models.RootResponse(message="欢迎使用 AgentBox 许可证注册服务")

@app.get("/health", tags=["Health"], summary="健康检查")
async def health_check():
    """
    健康检查接口，返回服务状态。
    """
    return models.HealthResponse()

@app.post("/register", response_model=models.RegisterResponse)
async def register(request: models.RegisterRequest) -> models.RegisterResponse:
    """
    注册客户端公钥
    
    接收客户端的 PEM 格式公钥并存储，用于后续的签名验证和加密操作。
    """
    # 检查设备是否已注册
    if usn := await mana.check_device_registered(
        request.system_uuid,
        request.baseboard_serial,
        request.disk_serial
    ):
        print(f"设备已注册，USN: {usn}")
        raise HTTPException(status_code=400, detail=f"设备已注册，无法重复注册。USN: {usn}")
    
    # 设备未注册，继续注册流程
    # 生成唯一序列号
    # 生成 ISO 日期（YYWW 格式）用于 USN 生成
    iso_date = mana.generate_iso_date()
    usn = await mana.generate_usn(
        request.device_model,
        request.manufacturer_id,
        iso_date,
    )

    device = models.Device(
        device_model=request.device_model,
        manufacturer_id=request.manufacturer_id,
        system_uuid=request.system_uuid,
        baseboard_serial=request.baseboard_serial,
        disk_serial=request.disk_serial,
        public_key_pem=request.public_key_pem,
        iso_date=iso_date,
        usn=usn
    )

    # 存储设备信息和公钥
    await mana.register_device(device)

    return models.RegisterResponse(usn=usn, message="注册成功")

@app.post("/verify-signature", response_model=models.VerifySignatureResponse)
async def verify_signature(request: models.VerifySignatureRequest) -> models.VerifySignatureResponse:
    """
    验证客户端签名
    
    使用存储的公钥验证客户端发送的消息签名，确保消息的完整性和真实性。
    """
    # 查找设备对应的公钥
    public_key_pem = await mana.get_public_key_by_usn(request.usn)
    if not public_key_pem:
        raise HTTPException(status_code=404, detail="未找到对应的设备或公钥")

    # 验证签名
    is_valid = mana.verify_signature1(
        public_key_pem,
        request.message,
        request.signature_b64
    )

    if is_valid:
        return models.VerifySignatureResponse(valid=True, detail="签名有效")
    else:
        return models.VerifySignatureResponse(valid=False, detail="签名无效")

async def main():
    """主函数:初始化数据库并启动服务器"""
    logger = await get_logger()
    
    # 读取配置文件
    config = configparser.ConfigParser()
    config.read('server.conf')
    
    # 数据库配置
    host = config.get('db', 'host')
    port = config.getint('db', 'port')
    user = config.get('db', 'user')
    password = config.get('db', 'password')
    dbname = config.get('db', 'dbname')
    
    # 服务器配置
    server_host = config.get('server', 'host', fallback='0.0.0.0')
    server_port = config.getint('server', 'port', fallback=8000)
    
    try:
        # ✅ 使用 await 初始化数据库
        await db.init(
            host=host, 
            port=port, 
            user=user, 
            password=password, 
            db=dbname
        )
        await logger.pInfo("[主程序] 数据库初始化成功")
        
        # ✅ 直接传递 app 对象而不是字符串
        config = Config(
            app=app,  # 直接使用导入的 app 对象
            host=server_host,
            port=server_port,
            log_level="info"
        )
        
        server = Server(config)
        await logger.pInfo(f"[主程序] 服务器启动在 {server_host}:{server_port}")
        
        await server.serve()
        
    except Exception as e:
        await logger.pError(f"[主程序] 启动失败: {e}")
        raise
    finally:
        # 清理资源
        await db.close_db()
        await logger.pInfo("[主程序] 数据库连接已关闭")
        await logger.flush()

if __name__ == "__main__":
    asyncio.run(main())