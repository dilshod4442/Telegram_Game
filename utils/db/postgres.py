from typing import Union, Optional, List, Dict, Any
import datetime
import asyncpg
from asyncpg import Connection
from asyncpg.pool import Pool

from data import config


class Database:
    def __init__(self):
        self.pool: Union[Pool, None] = None

    async def create(self):
        self.pool = await asyncpg.create_pool(
            user=config.DB_USER,
            password=config.DB_PASS,
            host=config.DB_HOST,
            database=config.DB_NAME,
        )

    async def execute(
        self,
        command,
        *args,
        fetch: bool = False,
        fetchval: bool = False,
        fetchrow: bool = False,
        execute: bool = False,
    ):
        async with self.pool.acquire() as connection:
            connection: Connection
            async with connection.transaction():
                if fetch:
                    result = await connection.fetch(command, *args)
                elif fetchval:
                    result = await connection.fetchval(command, *args)
                elif fetchrow:
                    result = await connection.fetchrow(command, *args)
                elif execute:
                    result = await connection.execute(command, *args)
            return result

    async def create_table_users(self):
        # 1. Таблица пользователей
        sql = """
        CREATE TABLE IF NOT EXISTS Users (
            id SERIAL PRIMARY KEY,
            full_name VARCHAR(255) NOT NULL,
            username VARCHAR(255) NULL,
            telegram_id BIGINT NOT NULL UNIQUE,
            first_name VARCHAR(255) NULL,
            last_name VARCHAR(255) NULL,
            phone VARCHAR(64) NULL,
            email VARCHAR(255) NULL,
            is_email_verified BOOLEAN DEFAULT FALSE,
            age INTEGER NULL,
            gender VARCHAR(32) NULL,
            location_lat DOUBLE PRECISION NULL,
            location_lon DOUBLE PRECISION NULL,
            location_address TEXT NULL,
            bio TEXT NULL,
            is_registered BOOLEAN DEFAULT FALSE,
            coins INTEGER DEFAULT 100,
            xp INTEGER DEFAULT 0,
            level INTEGER DEFAULT 1,
            hp INTEGER DEFAULT 100,
            max_hp INTEGER DEFAULT 100,
            attack INTEGER DEFAULT 15,
            defense INTEGER DEFAULT 10,
            games_played INTEGER DEFAULT 0,
            games_won INTEGER DEFAULT 0,
            daily_streak INTEGER DEFAULT 0,
            last_daily_claim TIMESTAMP NULL,
            total_messages INTEGER DEFAULT 0,
            last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        await self.execute(sql, execute=True)

        # 2. Авто-миграции столбцов
        migrations = [
            "ALTER TABLE Users ADD COLUMN IF NOT EXISTS first_name VARCHAR(255)",
            "ALTER TABLE Users ADD COLUMN IF NOT EXISTS last_name VARCHAR(255)",
            "ALTER TABLE Users ADD COLUMN IF NOT EXISTS phone VARCHAR(64)",
            "ALTER TABLE Users ADD COLUMN IF NOT EXISTS email VARCHAR(255)",
            "ALTER TABLE Users ADD COLUMN IF NOT EXISTS is_email_verified BOOLEAN DEFAULT FALSE",
            "ALTER TABLE Users ADD COLUMN IF NOT EXISTS age INTEGER",
            "ALTER TABLE Users ADD COLUMN IF NOT EXISTS gender VARCHAR(32)",
            "ALTER TABLE Users ADD COLUMN IF NOT EXISTS location_lat DOUBLE PRECISION",
            "ALTER TABLE Users ADD COLUMN IF NOT EXISTS location_lon DOUBLE PRECISION",
            "ALTER TABLE Users ADD COLUMN IF NOT EXISTS location_address TEXT",
            "ALTER TABLE Users ADD COLUMN IF NOT EXISTS bio TEXT",
            "ALTER TABLE Users ADD COLUMN IF NOT EXISTS is_registered BOOLEAN DEFAULT FALSE",
            "ALTER TABLE Users ADD COLUMN IF NOT EXISTS coins INTEGER DEFAULT 100",
            "ALTER TABLE Users ADD COLUMN IF NOT EXISTS xp INTEGER DEFAULT 0",
            "ALTER TABLE Users ADD COLUMN IF NOT EXISTS level INTEGER DEFAULT 1",
            "ALTER TABLE Users ADD COLUMN IF NOT EXISTS hp INTEGER DEFAULT 100",
            "ALTER TABLE Users ADD COLUMN IF NOT EXISTS max_hp INTEGER DEFAULT 100",
            "ALTER TABLE Users ADD COLUMN IF NOT EXISTS attack INTEGER DEFAULT 15",
            "ALTER TABLE Users ADD COLUMN IF NOT EXISTS defense INTEGER DEFAULT 10",
            "ALTER TABLE Users ADD COLUMN IF NOT EXISTS games_played INTEGER DEFAULT 0",
            "ALTER TABLE Users ADD COLUMN IF NOT EXISTS games_won INTEGER DEFAULT 0",
            "ALTER TABLE Users ADD COLUMN IF NOT EXISTS daily_streak INTEGER DEFAULT 0",
            "ALTER TABLE Users ADD COLUMN IF NOT EXISTS last_daily_claim TIMESTAMP NULL",
            "ALTER TABLE Users ADD COLUMN IF NOT EXISTS total_messages INTEGER DEFAULT 0",
            "ALTER TABLE Users ADD COLUMN IF NOT EXISTS last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
            "ALTER TABLE Users ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
            "ALTER TABLE Users ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
        ]
        for migration in migrations:
            try:
                await self.execute(migration, execute=True)
            except Exception:
                pass

        # 3. Таблица инвентаря
        await self.execute("""
        CREATE TABLE IF NOT EXISTS Inventory (
            id SERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL,
            item_id VARCHAR(64) NOT NULL,
            item_name VARCHAR(128) NOT NULL,
            item_type VARCHAR(64) NOT NULL,
            quantity INTEGER DEFAULT 1,
            is_equipped BOOLEAN DEFAULT FALSE
        );
        """, execute=True)

        # 4. Таблица Мирового Босса
        await self.execute("""
        CREATE TABLE IF NOT EXISTS WorldBoss (
            id SERIAL PRIMARY KEY,
            boss_name VARCHAR(128) NOT NULL,
            current_hp INTEGER NOT NULL,
            max_hp INTEGER NOT NULL,
            level INTEGER DEFAULT 1,
            is_defeated BOOLEAN DEFAULT FALSE
        );
        """, execute=True)

        # 5. Таблица транзакций (история расходов/доходов)
        await self.execute("""
        CREATE TABLE IF NOT EXISTS Transactions (
            id SERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL,
            amount INTEGER NOT NULL,
            category VARCHAR(64) NOT NULL,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """, execute=True)

        # 6. Таблица друзей
        await self.execute("""
        CREATE TABLE IF NOT EXISTS Friends (
            id SERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL,
            friend_id BIGINT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, friend_id)
        );
        """, execute=True)

        # Создаем первого босса, если еще нет
        boss = await self.execute("SELECT * FROM WorldBoss WHERE is_defeated = FALSE LIMIT 1", fetchrow=True)
        if not boss:
            await self.execute(
                "INSERT INTO WorldBoss (boss_name, current_hp, max_hp, level) VALUES ($1, $2, $3, $4)",
                "🔥 Древний Дракон", 5000, 5000, 1, execute=True
            )

    @staticmethod
    def format_args(sql, parameters: dict):
        sql += " AND ".join(
            [f"{item} = ${num}" for num, item in enumerate(parameters.keys(), start=1)]
        )
        return sql, tuple(parameters.values())

    async def add_user(self, full_name, username, telegram_id):
        sql = """
        INSERT INTO Users (full_name, username, telegram_id, last_active, total_messages)
        VALUES ($1, $2, $3, CURRENT_TIMESTAMP, 1)
        ON CONFLICT (telegram_id) DO UPDATE 
        SET full_name = EXCLUDED.full_name, 
            username = EXCLUDED.username,
            last_active = CURRENT_TIMESTAMP,
            total_messages = Users.total_messages + 1
        RETURNING *;
        """
        return await self.execute(sql, full_name, username, telegram_id, fetchrow=True)

    async def get_user(self, telegram_id: int):
        sql = "SELECT * FROM Users WHERE telegram_id = $1"
        return await self.execute(sql, telegram_id, fetchrow=True)

    async def track_activity(self, telegram_id: int):
        """Обновляет время активности и счетчик сообщений"""
        sql = """
        UPDATE Users 
        SET last_active = CURRENT_TIMESTAMP,
            total_messages = COALESCE(total_messages, 0) + 1
        WHERE telegram_id = $1
        """
        await self.execute(sql, telegram_id, execute=True)

    async def save_registration(
        self,
        telegram_id: int,
        first_name: str,
        last_name: str = None,
        phone: str = None,
        email: str = None,
        is_email_verified: bool = False,
        age: int = None,
        gender: str = None,
        location_lat: float = None,
        location_lon: float = None,
        location_address: str = None,
        bio: str = None,
    ):
        sql = """
        UPDATE Users 
        SET first_name = $1,
            last_name = $2,
            phone = $3,
            email = $4,
            is_email_verified = $5,
            age = $6,
            gender = $7,
            location_lat = $8,
            location_lon = $9,
            location_address = $10,
            bio = $11,
            is_registered = TRUE,
            updated_at = CURRENT_TIMESTAMP
        WHERE telegram_id = $12
        RETURNING *;
        """
        return await self.execute(
            sql,
            first_name,
            last_name,
            phone,
            email,
            is_email_verified,
            age,
            gender,
            location_lat,
            location_lon,
            location_address,
            bio,
            telegram_id,
            fetchrow=True,
        )

    async def update_user_field(self, telegram_id: int, field_name: str, value):
        allowed_fields = {
            "first_name", "last_name", "phone", "email", "is_email_verified",
            "age", "gender", "location_lat", "location_lon", "location_address",
            "bio", "is_registered", "coins", "xp", "level", "hp", "max_hp",
            "attack", "defense", "games_played", "games_won", "daily_streak"
        }
        if field_name not in allowed_fields:
            raise ValueError(f"Поле {field_name} недопустимо для обновления.")

        sql = f"""
        UPDATE Users 
        SET {field_name} = $1, updated_at = CURRENT_TIMESTAMP 
        WHERE telegram_id = $2
        RETURNING *;
        """
        return await self.execute(sql, value, telegram_id, fetchrow=True)

    # =========================================================================
    #  DAILY REWARDS (ЕЖЕДНЕВНАЯ НАГРАДА)
    # =========================================================================

    async def get_daily_status(self, telegram_id: int) -> dict:
        user = await self.get_user(telegram_id)
        if not user:
            return {"can_claim": False, "streak": 1, "remaining_seconds": 0}

        last_claim = user.get("last_daily_claim")
        current_streak = user.get("daily_streak") or 0

        if not last_claim:
            return {"can_claim": True, "streak": 1, "remaining_seconds": 0}

        now = datetime.datetime.now()
        delta = now - last_claim
        total_seconds = delta.total_seconds()

        # Если прошло меньше 24 часов (86400 сек) - нельзя забрать
        if total_seconds < 86400:
            return {
                "can_claim": False,
                "streak": current_streak,
                "remaining_seconds": int(86400 - total_seconds),
            }
        # Если прошло от 24 до 48 часов - продолжаем стрик
        elif total_seconds <= 172800:
            next_streak = current_streak + 1
            if next_streak > 7:
                next_streak = 1  # Зацикливаем неделю
            return {"can_claim": True, "streak": next_streak, "remaining_seconds": 0}
        # Если прошло больше 48 часов - стрик сгорел
        else:
            return {"can_claim": True, "streak": 1, "remaining_seconds": 0}

    async def claim_daily_reward(self, telegram_id: int) -> dict:
        status = await self.get_daily_status(telegram_id)
        if not status["can_claim"]:
            return {"success": False, "remaining_seconds": status["remaining_seconds"]}

        streak = status["streak"]
        # Награда: День 1: 50, День 2: 75, День 3: 100, ..., День 7: 300 coins
        rewards_coins = {1: 50, 2: 75, 3: 100, 4: 125, 5: 150, 6: 200, 7: 300}
        rewards_xp = {1: 20, 2: 30, 3: 40, 4: 50, 5: 60, 6: 80, 7: 150}

        coins_bonus = rewards_coins.get(streak, 50)
        xp_bonus = rewards_xp.get(streak, 20)

        sql = """
        UPDATE Users 
        SET coins = COALESCE(coins, 0) + $1,
            xp = COALESCE(xp, 0) + $2,
            daily_streak = $3,
            last_daily_claim = CURRENT_TIMESTAMP,
            level = 1 + (COALESCE(xp, 0) + $2) / 100
        WHERE telegram_id = $4
        RETURNING *;
        """
        updated = await self.execute(sql, coins_bonus, xp_bonus, streak, telegram_id, fetchrow=True)

        await self.add_transaction(
            user_id=telegram_id,
            amount=coins_bonus,
            category="daily",
            description=f"Ежедневная награда за день {streak}",
        )

        return {
            "success": True,
            "streak": streak,
            "coins": coins_bonus,
            "xp": xp_bonus,
            "total_coins": updated["coins"],
            "total_xp": updated["xp"],
            "level": updated["level"],
        }

    # =========================================================================
    #  МИНИ-ИГРЫ & ЭКОНОМИКА
    # =========================================================================

    async def record_game(self, telegram_id: int, won: bool, coins_delta: int, xp_delta: int, game_name: str = "Game"):
        """Записывает результат игры, начисляет или списывает монеты/XP, пересчитывает уровень"""
        sql = """
        UPDATE Users 
        SET games_played = COALESCE(games_played, 0) + 1,
            games_won = COALESCE(games_won, 0) + (CASE WHEN $1 THEN 1 ELSE 0 END),
            coins = GREATEST(0, COALESCE(coins, 0) + $2),
            xp = COALESCE(xp, 0) + $3,
            level = 1 + (COALESCE(xp, 0) + $3) / 100
        WHERE telegram_id = $4
        RETURNING *;
        """
        user = await self.execute(sql, won, coins_delta, xp_delta, telegram_id, fetchrow=True)

        if coins_delta != 0:
            category = "game_win" if coins_delta > 0 else "game_loss"
            await self.add_transaction(
                user_id=telegram_id,
                amount=coins_delta,
                category=category,
                description=f"Результат в игре {game_name}",
            )

        return user

    # =========================================================================
    #  ИНВЕНТАРЬ И МАГАЗИН (RPG)
    # =========================================================================

    async def get_inventory(self, telegram_id: int) -> List[dict]:
        sql = "SELECT * FROM Inventory WHERE user_id = $1 AND quantity > 0 ORDER BY id ASC"
        rows = await self.execute(sql, telegram_id, fetch=True)
        return [dict(r) for r in rows]

    async def add_inventory_item(self, telegram_id: int, item_id: str, item_name: str, item_type: str, quantity: int = 1):
        sql = """
        INSERT INTO Inventory (user_id, item_id, item_name, item_type, quantity)
        VALUES ($1, $2, $3, $4, $5)
        """
        # Если уже есть предмет такого типа, увеличиваем количество
        existing = await self.execute(
            "SELECT * FROM Inventory WHERE user_id = $1 AND item_id = $2",
            telegram_id, item_id, fetchrow=True
        )
        if existing:
            await self.execute(
                "UPDATE Inventory SET quantity = quantity + $1 WHERE id = $2",
                quantity, existing["id"], execute=True
            )
        else:
            await self.execute(sql, telegram_id, item_id, item_name, item_type, quantity, execute=True)

    async def use_inventory_item(self, telegram_id: int, item_id: str) -> dict:
        item = await self.execute(
            "SELECT * FROM Inventory WHERE user_id = $1 AND item_id = $2 AND quantity > 0",
            telegram_id, item_id, fetchrow=True
        )
        if not item:
            return {"success": False, "message": "Предмет не найден в инвентаре."}

        item_type = item["item_type"]
        effect_msg = ""

        if item_type == "potion":
            # Лечебное зелье восстанавливает 50 HP
            await self.execute(
                "UPDATE Users SET hp = LEAST(max_hp, hp + 50) WHERE telegram_id = $1",
                telegram_id, execute=True
            )
            effect_msg = "🧪 Вы выпили Зелье Здоровья и восстановили +50 HP!"
        elif item_type == "weapon":
            await self.execute(
                "UPDATE Users SET attack = attack + 10 WHERE telegram_id = $1",
                telegram_id, execute=True
            )
            effect_msg = "⚔️ Вы экипировали оружие! Атака увеличена на +10."
        elif item_type == "shield":
            await self.execute(
                "UPDATE Users SET defense = defense + 8 WHERE telegram_id = $1",
                telegram_id, execute=True
            )
            effect_msg = "🛡 Вы экипировали щит! Защита увеличена на +8."
        else:
            effect_msg = f"✨ Вы использовали {item['item_name']}!"

        # Уменьшаем количество на 1
        if item["quantity"] <= 1:
            await self.execute("DELETE FROM Inventory WHERE id = $1", item["id"], execute=True)
        else:
            await self.execute("UPDATE Inventory SET quantity = quantity - 1 WHERE id = $1", item["id"], execute=True)

        user = await self.get_user(telegram_id)
        return {"success": True, "message": effect_msg, "user": user}

    # =========================================================================
    #  МИРОВОЙ БОСС (WORLD BOSS)
    # =========================================================================

    async def get_world_boss(self) -> dict:
        sql = "SELECT * FROM WorldBoss WHERE is_defeated = FALSE ORDER BY id DESC LIMIT 1"
        boss = await self.execute(sql, fetchrow=True)
        if not boss:
            # Создаем нового босса
            await self.execute(
                "INSERT INTO WorldBoss (boss_name, current_hp, max_hp, level) VALUES ($1, $2, $3, $4)",
                "🔥 Древний Дракон", 5000, 5000, 1, execute=True
            )
            boss = await self.execute(sql, fetchrow=True)
        return dict(boss)

    async def attack_world_boss(self, telegram_id: int, user_attack: int) -> dict:
        boss = await self.get_world_boss()
        current_hp = boss["current_hp"]
        damage = max(5, user_attack)

        new_hp = max(0, current_hp - damage)
        is_dead = new_hp <= 0

        if is_dead:
            await self.execute(
                "UPDATE WorldBoss SET current_hp = 0, is_defeated = TRUE WHERE id = $1",
                boss["id"], execute=True
            )
            # Награда за добивание босса: +500 монет, +250 XP
            reward_coins = 500
            reward_xp = 250
            await self.execute(
                "UPDATE Users SET coins = coins + $1, xp = xp + $2, level = 1 + (xp + $2)/100 WHERE telegram_id = $3",
                reward_coins, reward_xp, telegram_id, execute=True
            )
            await self.add_transaction(telegram_id, reward_coins, "boss_kill", "Награда за победу над Мировым Боссом!")

            # Спавним нового более сильного босса
            next_lvl = boss["level"] + 1
            next_hp = 5000 + next_lvl * 1500
            next_names = ["⚡️ Титан Грома", "❄️ Ледяной Левиафан", "☠️ Повелитель Тьмы", "🌋 Огненный Голем"]
            next_name = next_names[(next_lvl - 1) % len(next_names)]
            await self.execute(
                "INSERT INTO WorldBoss (boss_name, current_hp, max_hp, level) VALUES ($1, $2, $3, $4)",
                f"{next_name} (Ур. {next_lvl})", next_hp, next_hp, next_lvl, execute=True
            )
        else:
            await self.execute(
                "UPDATE WorldBoss SET current_hp = $1 WHERE id = $2",
                new_hp, boss["id"], execute=True
            )
            # Награда за удар: +15 монет, +10 XP
            reward_coins = 15
            reward_xp = 10
            await self.execute(
                "UPDATE Users SET coins = coins + $1, xp = xp + $2, level = 1 + (xp + $2)/100 WHERE telegram_id = $3",
                reward_coins, reward_xp, telegram_id, execute=True
            )
            await self.add_transaction(telegram_id, reward_coins, "boss_hit", f"Урон по боссу: -{damage} HP")

        return {
            "damage": damage,
            "boss_name": boss["boss_name"],
            "current_hp": new_hp,
            "max_hp": boss["max_hp"],
            "is_defeated": is_dead,
            "reward_coins": reward_coins,
            "reward_xp": reward_xp,
        }

    # =========================================================================
    #  ТРАНЗАКЦИИ И РАСХОДЫ
    # =========================================================================

    async def add_transaction(self, user_id: int, amount: int, category: str, description: str):
        sql = """
        INSERT INTO Transactions (user_id, amount, category, description)
        VALUES ($1, $2, $3, $4)
        """
        await self.execute(sql, user_id, amount, category, description, execute=True)

    async def get_user_transactions(self, user_id: int, limit: int = 8) -> List[dict]:
        sql = "SELECT * FROM Transactions WHERE user_id = $1 ORDER BY id DESC LIMIT $2"
        rows = await self.execute(sql, user_id, limit, fetch=True)
        return [dict(r) for r in rows]

    async def get_spending_analytics(self, user_id: int) -> dict:
        sql = """
        SELECT 
            COALESCE(SUM(CASE WHEN amount > 0 THEN amount ELSE 0 END), 0) as income,
            COALESCE(SUM(CASE WHEN amount < 0 THEN ABS(amount) ELSE 0 END), 0) as expense,
            COUNT(*) as total_trans
        FROM Transactions WHERE user_id = $1
        """
        res = await self.execute(sql, user_id, fetchrow=True)
        return dict(res)

    # =========================================================================
    #  ДРУЗЬЯ (СОЦИАЛЬНЫЕ ФУНКЦИИ)
    # =========================================================================

    async def add_friend(self, user_id: int, friend_id: int) -> bool:
        if user_id == friend_id:
            return False
        sql = """
        INSERT INTO Friends (user_id, friend_id)
        VALUES ($1, $2)
        ON CONFLICT (user_id, friend_id) DO NOTHING
        """
        await self.execute(sql, user_id, friend_id, execute=True)
        return True

    async def get_friends(self, user_id: int) -> List[dict]:
        sql = """
        SELECT u.telegram_id, u.first_name, u.full_name, u.username, u.level, u.xp
        FROM Friends f
        JOIN Users u ON f.friend_id = u.telegram_id
        WHERE f.user_id = $1
        ORDER BY f.id DESC
        """
        rows = await self.execute(sql, user_id, fetch=True)
        return [dict(r) for r in rows]

    async def remove_friend(self, user_id: int, friend_id: int):
        await self.execute("DELETE FROM Friends WHERE user_id = $1 AND friend_id = $2", user_id, friend_id, execute=True)

    # =========================================================================
    #  РЕЙТИНГИ (LEADERBOARDS)
    # =========================================================================

    async def get_leaderboard(self, category: str = "xp", limit: int = 10) -> List[dict]:
        col = "xp"
        if category == "coins":
            col = "coins"
        elif category == "wins":
            col = "games_won"
        elif category == "streak":
            col = "daily_streak"

        sql = f"""
        SELECT telegram_id, COALESCE(first_name, full_name) as name, username, level, xp, coins, games_won, daily_streak
        FROM Users
        ORDER BY {col} DESC NULLS LAST
        LIMIT $1
        """
        rows = await self.execute(sql, limit, fetch=True)
        return [dict(r) for r in rows]

    # =========================================================================
    #  ГЛОБАЛЬНАЯ СТАТИСТИКА И ПОИСК
    # =========================================================================

    async def get_global_stats(self) -> dict:
        total_users = await self.execute("SELECT COUNT(*) FROM Users", fetchval=True)
        
        # Активные сегодня
        active_today = await self.execute(
            "SELECT COUNT(*) FROM Users WHERE last_active >= CURRENT_DATE", fetchval=True
        )
        # Новые сегодня
        new_today = await self.execute(
            "SELECT COUNT(*) FROM Users WHERE created_at >= CURRENT_DATE", fetchval=True
        )
        # Сообщений сегодня
        total_msgs = await self.execute(
            "SELECT COALESCE(SUM(total_messages), 0) FROM Users", fetchval=True
        )
        # Всего игр
        total_games = await self.execute(
            "SELECT COALESCE(SUM(games_played), 0) FROM Users", fetchval=True
        )
        # Всего транзакций
        total_trans = await self.execute(
            "SELECT COUNT(*) FROM Transactions", fetchval=True
        )
        # Зарегистрированных
        registered = await self.execute(
            "SELECT COUNT(*) FROM Users WHERE is_registered = TRUE", fetchval=True
        )

        return {
            "users": total_users or 0,
            "registered": registered or 0,
            "active_today": active_today or 0,
            "new_today": new_today or 0,
            "messages_today": total_msgs or 0,
            "games": total_games or 0,
            "transactions": total_trans or 0,
        }

    async def search_user(self, query: str) -> Optional[dict]:
        clean = query.strip().lstrip("@")
        if clean.isdigit():
            user = await self.execute(
                "SELECT * FROM Users WHERE telegram_id = $1", int(clean), fetchrow=True
            )
            if user:
                return dict(user)

        user = await self.execute(
            "SELECT * FROM Users WHERE LOWER(username) = LOWER($1)", clean, fetchrow=True
        )
        if user:
            return dict(user)

        # Поиск по имени
        user = await self.execute(
            "SELECT * FROM Users WHERE LOWER(first_name) LIKE LOWER($1) OR LOWER(full_name) LIKE LOWER($1) LIMIT 1",
            f"%{clean}%", fetchrow=True
        )
        return dict(user) if user else None

    # =========================================================================
    #  БАЗОВЫЕ МЕТОДЫ
    # =========================================================================

    async def select_all_users(self):
        sql = "SELECT * FROM Users ORDER BY id ASC"
        return await self.execute(sql, fetch=True)

    async def count_users(self):
        sql = "SELECT COUNT(*) FROM Users"
        return await self.execute(sql, fetchval=True)

    async def count_registered_users(self):
        sql = "SELECT COUNT(*) FROM Users WHERE is_registered = TRUE"
        return await self.execute(sql, fetchval=True)

    async def count_verified_emails(self):
        sql = "SELECT COUNT(*) FROM Users WHERE is_email_verified = TRUE"
        return await self.execute(sql, fetchval=True)

    async def delete_users(self):
        await self.execute("DELETE FROM Users WHERE TRUE", execute=True)

    async def drop_users(self):
        await self.execute("DROP TABLE Users", execute=True)
