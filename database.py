import asyncpg
import os
DATABASE_URL = os.environ.get("postgres://avnadmin:AVNS_xePgM_KGoKWdYCRItQr@pg-38383ef6-kf677.e.aivencloud.com:23673/defaultdb?sslmode=require")

class Database:
    def __init__(self):
        self.pool = None

    async def connect(self):
        """Создаём пул соединений к Aiven"""
        self.pool = await asyncpg.create_pool(
            DATABASE_URL,
            min_size=1,
            max_size=5
        )
        await self.create_tables()
        print("✅ Подключено к Aiven PostgreSQL")

    async def create_tables(self):
        """Создаём таблицы, если их нет"""
        async with self.pool.acquire() as conn:
            # Таблица игроков
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS players (
                    user_id BIGINT PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Таблица мутов
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS mutes (
                    user_id BIGINT PRIMARY KEY,
                    muted_until TIMESTAMP,
                    reason TEXT
                )
            ''')

            # Таблица лобби для 2х2
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS lobbies_2x2 (
                    lobby_id SERIAL PRIMARY KEY,
                    player1_id BIGINT,
                    player2_id BIGINT,
                    status TEXT DEFAULT 'waiting',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            print("✅ Таблицы созданы (или уже существуют)")

    # ---------- МЕТОДЫ ДЛЯ РАБОТЫ С ИГРОКАМИ ----------
    async def register_player(self, user_id: int, username: str, first_name: str):
        """Регистрируем игрока при первом запуске"""
        async with self.pool.acquire() as conn:
            await conn.execute('''
                INSERT INTO players (user_id, username, first_name)
                VALUES ($1, $2, $3)
                ON CONFLICT (user_id) DO UPDATE 
                SET username = $2, first_name = $3
            ''', user_id, username, first_name)

    async def get_player(self, user_id: int):
        """Получить данные игрока"""
        async with self.pool.acquire() as conn:
            return await conn.fetchrow(
                "SELECT * FROM players WHERE user_id = $1", user_id
            )

    # ---------- МЕТОДЫ ДЛЯ МУТОВ ----------
    async def is_muted(self, user_id: int) -> bool:
        """Проверить, есть ли активный мут"""
        async with self.pool.acquire() as conn:
            result = await conn.fetchval('''
                SELECT muted_until > CURRENT_TIMESTAMP 
                FROM mutes 
                WHERE user_id = $1
            ''', user_id)
            return result or False

    async def mute_user(self, user_id: int, minutes: int = 5, reason: str = "Не подтвердил матч"):
        """Замутить игрока на N минут"""
        async with self.pool.acquire() as conn:
            await conn.execute('''
                INSERT INTO mutes (user_id, muted_until, reason)
                VALUES ($1, CURRENT_TIMESTAMP + INTERVAL '1 minute' * $2, $3)
                ON CONFLICT (user_id) DO UPDATE 
                SET muted_until = CURRENT_TIMESTAMP + INTERVAL '1 minute' * $2,
                    reason = $3
            ''', user_id, minutes, reason)

    # ---------- МЕТОДЫ ДЛЯ ЛОББИ 2Х2 ----------
    async def add_to_lobby_2x2(self, user_id: int) -> int:
        """Добавить игрока в лобби 2х2. Возвращает lobby_id"""
        async with self.pool.acquire() as conn:
            # Ищем свободное лобби (где меньше 2 игроков и статус waiting)
            lobby = await conn.fetchrow('''
                SELECT lobby_id, player1_id, player2_id 
                FROM lobbies_2x2 
                WHERE status = 'waiting' 
                  AND (player1_id IS NULL OR player2_id IS NULL)
                LIMIT 1
            ''')
            
            if lobby:
                lobby_id = lobby['lobby_id']
                if lobby['player1_id'] is None:
                    await conn.execute(
                        "UPDATE lobbies_2x2 SET player1_id = $1 WHERE lobby_id = $2",
                        user_id, lobby_id
                    )
                else:
                    await conn.execute(
                        "UPDATE lobbies_2x2 SET player2_id = $1 WHERE lobby_id = $2",
                        user_id, lobby_id
                    )
                return lobby_id
            else:
                # Создаём новое лобби
                lobby_id = await conn.fetchval('''
                    INSERT INTO lobbies_2x2 (player1_id) 
                    VALUES ($1) 
                    RETURNING lobby_id
                ''', user_id)
                return lobby_id

    async def get_lobby_2x2(self, lobby_id: int):
        """Получить данные лобби"""
        async with self.pool.acquire() as conn:
            return await conn.fetchrow(
                "SELECT * FROM lobbies_2x2 WHERE lobby_id = $1", lobby_id
            )

    async def is_lobby_full_2x2(self, lobby_id: int) -> bool:
        """Проверить, заполнено ли лобби (2 игрока)"""
        async with self.pool.acquire() as conn:
            result = await conn.fetchval('''
                SELECT COUNT(*) 
                FROM lobbies_2x2 
                WHERE lobby_id = $1 
                  AND player1_id IS NOT NULL 
                  AND player2_id IS NOT NULL
            ''', lobby_id)
            return result == 1

    async def remove_from_lobby_2x2(self, user_id: int, lobby_id: int):
        """Удалить игрока из лобби"""
        async with self.pool.acquire() as conn:
            lobby = await self.get_lobby_2x2(lobby_id)
            if lobby['player1_id'] == user_id:
                await conn.execute(
                    "UPDATE lobbies_2x2 SET player1_id = NULL WHERE lobby_id = $1",
                    lobby_id
                )
            elif lobby['player2_id'] == user_id:
                await conn.execute(
                    "UPDATE lobbies_2x2 SET player2_id = NULL WHERE lobby_id = $1",
                    lobby_id
                )
            
            # Если оба слота пустые — удаляем лобби
            lobby = await self.get_lobby_2x2(lobby_id)
            if lobby['player1_id'] is None and lobby['player2_id'] is None:
                await conn.execute(
                    "DELETE FROM lobbies_2x2 WHERE lobby_id = $1", lobby_id
                )
