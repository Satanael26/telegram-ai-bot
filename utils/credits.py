import os
import sqlite3
from datetime import datetime, date

# Path de la base de datos
DB_PATH = os.getenv("DB_PATH") or "bot_data.sqlite"

# Tiers de suscripción
SUBSCRIPTION_TIERS = {
    "free": {
        "name": "Free",
        "daily_limit": 5,
        "monthly_limit": 50,
        "price": 0,
        "features": ["Generador básico", "Máx 5 imágenes/día"]
    },
    "basic": {
        "name": "Basic",
        "daily_limit": 100,
        "monthly_limit": 500,
        "price": 29,
        "features": ["Generador con estilos", "500 imágenes/mes"]
    },
    "pro": {
        "name": "Pro",
        "daily_limit": 200,
        "monthly_limit": 2000,
        "price": 49,
        "features": ["Todos los estilos", "Captions IA", "2000 imágenes/mes"]
    },
    "agency": {
        "name": "Agency",
        "daily_limit": 500,
        "monthly_limit": 999999,
        "price": 99,
        "features": ["Todo ilimitado", "3 cuentas", "Soporte prioritario"]
    }
}


def init_db():
    """Crea las tablas necesarias si no existen."""
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                telegram_id INTEGER PRIMARY KEY,
                credits INTEGER NOT NULL DEFAULT 0,
                is_admin INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                last_daily_bonus TEXT,
                subscription_tier TEXT NOT NULL DEFAULT 'free',
                stripe_customer_id TEXT,
                stripe_subscription_id TEXT,
                subscription_expires_at TEXT
            )
            """
        )
        # Agregar columnas si no existen (para usuarios existentes)
        try:
            cur.execute("ALTER TABLE users ADD COLUMN last_daily_bonus TEXT")
        except sqlite3.OperationalError:
            pass
        
        try:
            cur.execute("ALTER TABLE users ADD COLUMN subscription_tier TEXT NOT NULL DEFAULT 'free'")
        except sqlite3.OperationalError:
            pass
        
        try:
            cur.execute("ALTER TABLE users ADD COLUMN stripe_customer_id TEXT")
        except sqlite3.OperationalError:
            pass
        
        try:
            cur.execute("ALTER TABLE users ADD COLUMN stripe_subscription_id TEXT")
        except sqlite3.OperationalError:
            pass
        
        try:
            cur.execute("ALTER TABLE users ADD COLUMN subscription_expires_at TEXT")
        except sqlite3.OperationalError:
            pass
        
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER NOT NULL,
                kind TEXT NOT NULL,
                amount INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(telegram_id) REFERENCES users(telegram_id)
            )
            """
        )
        conn.commit()


def _ensure_user(telegram_id: int):
    """Crea un usuario en la DB si no existe con 100 créditos iniciales."""
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("SELECT telegram_id FROM users WHERE telegram_id = ?", (telegram_id,))
        if not cur.fetchone():
            cur.execute(
                "INSERT INTO users(telegram_id, credits, is_admin, created_at) VALUES(?,?,?,?)",
                (telegram_id, 100, 0, datetime.utcnow().isoformat()),
            )
            conn.commit()


def get_credits(telegram_id: int) -> int:
    """Obtiene el saldo de créditos de un usuario."""
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("SELECT credits FROM users WHERE telegram_id = ?", (telegram_id,))
        row = cur.fetchone()
        return row[0] if row else 0


def add_credits(telegram_id: int, amount: int, kind: str = "manual"):
    """Añade créditos a un usuario y registra la transacción."""
    _ensure_user(telegram_id)
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("UPDATE users SET credits = credits + ? WHERE telegram_id = ?", (amount, telegram_id))
        cur.execute(
            "INSERT INTO transactions(telegram_id, kind, amount, created_at) VALUES(?,?,?,?)",
            (telegram_id, kind, amount, datetime.utcnow().isoformat()),
        )
        conn.commit()


def consume_credits(telegram_id: int, amount: int) -> bool:
    """Intenta consumir créditos. Devuelve True si tuvo suficientes, False si no."""
    _ensure_user(telegram_id)
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("SELECT credits FROM users WHERE telegram_id = ?", (telegram_id,))
        row = cur.fetchone()
        credits = row[0] if row else 0
        
        if credits < amount:
            return False
        
        cur.execute("UPDATE users SET credits = credits - ? WHERE telegram_id = ?", (amount, telegram_id))
        cur.execute(
            "INSERT INTO transactions(telegram_id, kind, amount, created_at) VALUES(?,?,?,?)",
            (telegram_id, "consume", -amount, datetime.utcnow().isoformat()),
        )
        conn.commit()
        return True


def claim_daily_bonus(telegram_id: int) -> bool:
    """Intenta reclamar el bonus diario de 45 créditos. Devuelve True si se otorgó, False si ya lo reclamó hoy."""
    _ensure_user(telegram_id)
    today = date.today().isoformat()
    
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("SELECT last_daily_bonus FROM users WHERE telegram_id = ?", (telegram_id,))
        row = cur.fetchone()
        last_bonus_date = row[0] if row else None
        
        # Si ya reclamó hoy, no otorgar bonus
        if last_bonus_date == today:
            return False
        
        # Otorgar 45 créditos
        cur.execute("UPDATE users SET credits = credits + 45 WHERE telegram_id = ?", (telegram_id,))
        cur.execute("UPDATE users SET last_daily_bonus = ? WHERE telegram_id = ?", (today, telegram_id))
        cur.execute(
            "INSERT INTO transactions(telegram_id, kind, amount, created_at) VALUES(?,?,?,?)",
            (telegram_id, "daily_bonus", 45, datetime.utcnow().isoformat()),
        )
        conn.commit()
        return True


def is_admin(telegram_id: int, admin_ids: set) -> bool:
    """Verifica si un usuario es administrador."""
    return telegram_id in admin_ids


# NUEVAS FUNCIONES PARA SUSCRIPCIÓN
def get_user_subscription(telegram_id: int) -> dict:
    """Obtiene la suscripción actual del usuario."""
    _ensure_user(telegram_id)
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("SELECT subscription_tier, subscription_expires_at FROM users WHERE telegram_id = ?", (telegram_id,))
        row = cur.fetchone()
        if row:
            tier, expires = row
            # Verificar si la suscripción expiró
            if expires:
                if datetime.fromisoformat(expires) < datetime.utcnow():
                    # Renovar a free
                    set_user_subscription(telegram_id, "free")
                    return {"tier": "free", "info": SUBSCRIPTION_TIERS["free"]}
            return {"tier": tier or "free", "info": SUBSCRIPTION_TIERS.get(tier or "free", SUBSCRIPTION_TIERS["free"])}
        return {"tier": "free", "info": SUBSCRIPTION_TIERS["free"]}


def set_user_subscription(telegram_id: int, tier: str, expires_at: str = None):
    """Asigna una suscripción a un usuario."""
    if tier not in SUBSCRIPTION_TIERS:
        tier = "free"
    
    _ensure_user(telegram_id)
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute(
            "UPDATE users SET subscription_tier = ?, subscription_expires_at = ? WHERE telegram_id = ?",
            (tier, expires_at, telegram_id)
        )
        cur.execute(
            "INSERT INTO transactions(telegram_id, kind, amount, created_at) VALUES(?,?,?,?)",
            (telegram_id, f"subscription_{tier}", 0, datetime.utcnow().isoformat()),
        )
        conn.commit()


def set_stripe_customer(telegram_id: int, stripe_customer_id: str, stripe_subscription_id: str = None):
    """Asigna IDs de Stripe al usuario."""
    _ensure_user(telegram_id)
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute(
            "UPDATE users SET stripe_customer_id = ?, stripe_subscription_id = ? WHERE telegram_id = ?",
            (stripe_customer_id, stripe_subscription_id, telegram_id)
        )
        conn.commit()


def get_stripe_customer_id(telegram_id: int) -> str:
    """Obtiene el stripe_customer_id de un usuario."""
    _ensure_user(telegram_id)
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("SELECT stripe_customer_id FROM users WHERE telegram_id = ?", (telegram_id,))
        row = cur.fetchone()
        return row[0] if row and row[0] else None


def check_usage_limit(telegram_id: int, operation_cost: int = 1) -> dict:
    """Verifica si el usuario puede hacer una operación según su tier y límite diario."""
    sub = get_user_subscription(telegram_id)
    tier_info = sub["info"]
    
    # Por ahora usamos créditos, pero aquí puedes agregar lógica de límites diarios
    credits = get_credits(telegram_id)
    
    return {
        "allowed": credits >= operation_cost,
        "credits": credits,
        "tier": sub["tier"],
        "daily_limit": tier_info.get("daily_limit", 5),
        "monthly_limit": tier_info.get("monthly_limit", 50)
    }
