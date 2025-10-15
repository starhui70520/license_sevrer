from pydantic import BaseModel, Field

# API 请求和响应模型

class RegisterRequest(BaseModel):
    """注册请求"""
    device_model: str = Field(..., description="设备型号")
    manufacturer_id: str = Field(..., description="制造商 ID")
    system_uuid: str = Field(..., description="系统 UUID")
    baseboard_serial: str = Field(..., description="主板序列号")
    disk_serial: str = Field(..., description="系统盘序列号")
    public_key_pem: str = Field(..., min_length=100, description="PEM 格式的公钥")

class VerifySignatureRequest(BaseModel):
    """验证签名请求"""
    usn: str = Field(..., description="分配的唯一序列号")
    message: str = Field(..., description="原始消息")
    signature_b64: str = Field(..., description="Base64 编码的签名")

class RootResponse(BaseModel):
    """根响应"""
    message: str

class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str = Field(default="ok")

class RegisterResponse(BaseModel):
    """注册响应"""
    usn: str = Field(..., description="分配的唯一序列号")
    message: str = Field(..., description="响应消息")

class VerifySignatureResponse(BaseModel):
    """验证签名响应"""
    valid: bool = Field(..., description="签名是否有效")
    detail: str = Field(..., description="详细信息")

# 数据库模型
class Device(BaseModel):
    """设备模型"""
    device_model: str
    manufacturer_id: str
    system_uuid: str
    baseboard_serial: str
    disk_serial: str
    iso_date: str
    public_key_pem: str
    usn: str


