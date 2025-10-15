# db.py
import aiomysql
from contextlib import asynccontextmanager
from typing import List, Dict, Any, Optional
from logger import get_logger


class LicenseDB:
    """
    License 许可证数据库
    模块级单例含义：本模块只会创建一个 LicenseDB 实例。
    你可以在任何模块 import 并直接使用同一个实例：
        from db import db
    """

    def __init__(self):
        self._pool: Optional[aiomysql.Pool] = None

    async def init(
        self,
        host: str,
        port: int,
        user: str,
        password: str,
        db: str,
        minsize: int = 1,
        maxsize: int = 10,
    ):
        
        self.logger = await get_logger()
        
        """初始化连接池"""
        if self._pool is not None:
            await self.logger.pWarning("[数据库服务] 连接池已存在，跳过初始化")
            return

        try:
            self._pool = await aiomysql.create_pool(
                host=host,
                port=port,
                user=user,
                password=password,
                db=db,
                minsize=minsize,
                maxsize=maxsize,
                autocommit=True,
                charset="utf8mb4",
            )
            await self.logger.pInfo("[数据库服务] DB连接池初始化完成")
        except Exception as e:
            await self.logger.pError(f"[数据库服务] 连接池初始化失败: {e}")
            raise

    async def close_db(self):
        """关闭连接池"""
        if self._pool:
            self._pool.close()
            await self._pool.wait_closed()
            self._pool = None
            await self.logger.pInfo("[数据库服务] DB连接池已关闭")

    @property
    def pool(self) -> aiomysql.Pool:
        """获取连接池"""
        if not self._pool:
            raise RuntimeError("[数据库服务] 连接池未初始化，请先调用 db.init()")
        return self._pool

    # ==================== 连接上下文 ====================
    @asynccontextmanager
    async def connection(self):
        """获取数据库连接"""
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                yield cursor

    # ==================== 通用数据库操作 ====================
    async def execute(self, sql: str, params: tuple = None) -> int:
        """执行 INSERT / UPDATE / DELETE"""
        async with self.connection() as cur:
            rows = await cur.execute(sql, params)
            return rows

    async def execute_many(self, sql: str, params_list: List[tuple]) -> int:
        """批量执行"""
        async with self.connection() as cur:
            rows = await cur.executemany(sql, params_list)
            return rows

    async def fetch_one(self, sql: str, params: tuple = None) -> Optional[Dict[str, Any]]:
        """查询单条"""
        async with self.connection() as cur:
            await cur.execute(sql, params)
            return await cur.fetchone()

    async def fetch_all(self, sql: str, params: tuple = None) -> List[Dict[str, Any]]:
        """查询多条"""
        async with self.connection() as cur:
            await cur.execute(sql, params)
            return await cur.fetchall()

    async def fetch_many(self, sql: str, size: int, params: tuple = None) -> List[Dict[str, Any]]:
        """查询指定数量"""
        async with self.connection() as cur:
            await cur.execute(sql, params)
            return await cur.fetchmany(size)

    async def insert(self, table: str, data: Dict[str, Any]) -> int:
        """插入记录"""
        keys = ", ".join(data.keys())
        placeholders = ", ".join(["%s"] * len(data))
        sql = f"INSERT INTO {table} ({keys}) VALUES ({placeholders})"

        async with self.connection() as cur:
            await cur.execute(sql, tuple(data.values()))
            return cur.lastrowid

    async def update(
        self, table: str, data: Dict[str, Any], where: str, where_params: tuple = None
    ) -> int:
        """更新记录"""
        set_clause = ", ".join([f"{k} = %s" for k in data.keys()])
        sql = f"UPDATE {table} SET {set_clause} WHERE {where}"
        params = tuple(data.values()) + (where_params or ())
        return await self.execute(sql, params)

    async def delete(self, table: str, where: str, where_params: tuple = None) -> int:
        """删除记录"""
        sql = f"DELETE FROM {table} WHERE {where}"
        return await self.execute(sql, where_params)

    async def table_exists(self, table_name: str) -> bool:
        """检查表是否存在"""
        sql = """
        SELECT COUNT(*) AS count
        FROM information_schema.tables
        WHERE table_schema = %s AND table_name = %s
        """
        result = await self.fetch_one(sql, (self.pool.db.decode(), table_name))
        return result and result["count"] > 0


# ==================== 模块级单例 ====================
db = LicenseDB()
