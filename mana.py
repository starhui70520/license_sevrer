from db import db
from datetime import datetime
from models import Device
import base64
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.backends import default_backend
from cryptography.exceptions import InvalidSignature

async def check_device_registered(system_uuid: str, baseboard_serial: str, disk_serial: str) -> str:
    """
    检查设备是否已注册
    
    :param system_uuid: 系统UUID
    :baseboard_serial: 主板序列号
    :disk_serial: 系统盘序列号

    :return: 如果设备已注册返回 usn，否则返回空字符串
    """

    sql = """
        SELECT usn 
        FROM devices 
        WHERE system_uuid = %s 
        AND baseboard_serial = %s 
        AND disk_serial = %s
    """
    result = await db.fetch_one(sql, (system_uuid, baseboard_serial, disk_serial))
    return result['usn'] if result else ""

def generate_iso_date() -> str:
    """
    生成YYWW格式的ISO日期
    
    :return: YYWW格式的日期字符串(例如 '2512' 表示2025年第12周)
    """
    now = datetime.now()
    year = now.strftime('%y')  # 两位数年份
    week = now.isocalendar()[1]  # ISO周数
    return f"{year}{week:02d}"

async def generate_usn(device_model: str, manufacturer_id: str, iso_date: str) -> str:
    """
    生成唯一序列号
    
    :param device_model: 设备型号
    :param manufacturer_id: 制造商ID
    :param iso_date: ISO日期(YYWW格式,例如 '2512')
    :return: 生成的USN
    """
    
    # 查询当前序列号
    sql = """
        SELECT COUNT(*) as count 
        FROM devices 
        WHERE device_model = %s 
        AND manufacturer_id = %s 
        AND iso_date = %s
    """
    result = await db.fetch_one(sql, (device_model, manufacturer_id, iso_date))
    seq = result['count'] + 1 if result else 1
    
    return f"{device_model}{manufacturer_id}{iso_date}{seq:03d}"

async def register_device(device: Device) -> bool:
    """
    注册设备信息和公钥
    
    :param device: 设备信息和公钥
    其中 device 包含以下字段:
        - system_uuid: 系统UUID
        - baseboard_serial: 主板序列号
        - disk_serial: 系统盘序列号
        - public_key_pem: PEM格式的公钥
        - usn: 分配的唯一序列号
    这些字段将被存储到数据库中。
    :return: 是否注册成功
    """
    
    data = {
        "system_uuid": device.system_uuid,
        "baseboard_serial": device.baseboard_serial,
        "disk_serial": device.disk_serial,
        "public_key": device.public_key_pem,
        "usn": device.usn,
        "device_model": device.device_model,
        "manufacturer_id": device.manufacturer_id,
        "iso_date": device.iso_date,
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    }
    await db.insert("devices", data)

    return True

async def get_public_key_by_usn(usn: str) -> str:
    """
    根据USN获取设备公钥
    
    :param usn: 设备的唯一序列号
    :return: PEM格式的公钥，如果未找到返回空字符串
    """
    
    sql = "SELECT public_key FROM devices WHERE usn = %s"
    result = await db.fetch_one(sql, (usn,))
    return result['public_key'] if result else ""

def verify_signature1(public_key_pem: str, message: str, signature_b64: str) -> bool:
    """
    验证 RSA 签名（兼容 TPM 和软件实现）
    
    Args:
        public_key_pem: PEM 格式的公钥字符串
        message: 原始消息字符串
        signature_b64: Base64 编码的签名
        
    Returns:
        bool: 签名是否有效
    """
    try:
        print(f"\n=== 开始验证签名 ===")
        print(f"消息: {message}")
        print(f"消息长度: {len(message)} 字节")
        print(f"签名 (Base64): {signature_b64[:50]}...")
        
        # 1. 解码 Base64 签名
        signature = base64.b64decode(signature_b64)
        print(f"签名长度: {len(signature)} 字节")
        
        # 2. 加载公钥
        public_key = serialization.load_pem_public_key(
            public_key_pem.encode('utf-8'),
            backend=default_backend()
        )
        print(f"公钥类型: {type(public_key).__name__}")
        print(f"公钥长度: {public_key.key_size} bits")
        
        # 3. 尝试方式1：PKCS1v15 直接对消息签名（标准 RSA 签名）
        print("\n[方式1] PKCS1v15 + SHA256 对原始消息直接签名...")
        try:
            public_key.verify(
                signature,
                message.encode('utf-8'),
                padding.PKCS1v15(),
                hashes.SHA256()
            )
            print("✓ 签名验证成功！")
            print("   签名方式：RSA-PKCS1v15 + SHA256（标准方式）")
            return True
        except InvalidSignature:
            print(f"✗ 方式1验证失败")
        
        # 4. 尝试方式2：对预计算哈希签名（某些 TPM 实现）
        print("\n[方式2] PKCS1v15 对 SHA256 哈希值签名...")
        try:
            from cryptography.hazmat.primitives.asymmetric import utils
            
            # 先计算消息的 SHA256 哈希
            digest = hashes.Hash(hashes.SHA256(), backend=default_backend())
            digest.update(message.encode('utf-8'))
            message_hash = digest.finalize()
            print(f"消息哈希 (SHA256): {message_hash.hex()[:32]}...")
            
            # 使用 Prehashed 方式验证
            public_key.verify(
                signature,
                message_hash,
                padding.PKCS1v15(),
                utils.Prehashed(hashes.SHA256())
            )
            print("✓ 签名验证成功！")
            print("   签名方式：对预计算哈希签名（特殊 TPM 模式）")
            return True
        except InvalidSignature:
            print(f"✗ 方式2验证失败")
        
        # 5. 尝试 PSS padding（以防万一）
        print("\n[方式3] 尝试 PSS padding...")
        try:
            public_key.verify(
                signature,
                message.encode('utf-8'),
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            print("✓ 签名验证成功 (PSS padding)")
            return True
        except InvalidSignature:
            print(f"✗ PSS padding 验证失败")
        
        print("\n✗ 所有验证方式都失败")
        return False
        
    except Exception as e:
        print(f"\n✗ 验证签名时发生错误: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False