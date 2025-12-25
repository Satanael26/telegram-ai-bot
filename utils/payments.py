import os
import stripe
import logging
from datetime import datetime, timedelta
from utils.credits import (
    set_user_subscription, 
    set_stripe_customer, 
    get_stripe_customer_id,
    SUBSCRIPTION_TIERS,
    add_credits
)

logger = logging.getLogger(__name__)

# Inicializar Stripe
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
STRIPE_PUBLISHABLE_KEY = os.getenv("STRIPE_PUBLISHABLE_KEY")
WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")

# Precios de Stripe (debes crear estos en tu dashboard de Stripe)
STRIPE_PRICES = {
    "basic": os.getenv("STRIPE_PRICE_BASIC"),      # $29/mes
    "pro": os.getenv("STRIPE_PRICE_PRO"),          # $49/mes
    "agency": os.getenv("STRIPE_PRICE_AGENCY")     # $99/mes
}


def create_payment_link(telegram_id: int, tier: str) -> str:
    """
    Crea un link de pago para una suscripción.
    
    Args:
        telegram_id: ID del usuario de Telegram
        tier: Tier de suscripción (basic, pro, agency)
        
    Returns:
        str: URL de pago
    """
    if tier not in STRIPE_PRICES or not STRIPE_PRICES[tier]:
        raise ValueError(f"Tier inválido o precio no configurado: {tier}")
    
    try:
        # Crear o obtener customer
        stripe_customer_id = get_stripe_customer_id(telegram_id)
        
        if not stripe_customer_id:
            # Crear nuevo customer
            customer = stripe.Customer.create(
                metadata={"telegram_id": str(telegram_id)},
                description=f"Telegram user {telegram_id}"
            )
            stripe_customer_id = customer.id
            set_stripe_customer(telegram_id, stripe_customer_id)
        
        # Crear checkout session
        session = stripe.checkout.Session.create(
            customer=stripe_customer_id,
            payment_method_types=["card"],
            line_items=[
                {
                    "price": STRIPE_PRICES[tier],
                    "quantity": 1,
                }
            ],
            mode="subscription",
            success_url=f"https://t.me/TU_BOT?start=payment_success_{telegram_id}",
            cancel_url=f"https://t.me/TU_BOT",
            metadata={"telegram_id": str(telegram_id), "tier": tier}
        )
        
        return session.url
        
    except stripe.error.StripeError as e:
        logger.error(f"Error creating payment link for {telegram_id}: {e}")
        raise


def create_trial_subscription(telegram_id: int, tier: str, trial_days: int = 7):
    """
    Crea una suscripción de prueba (sin cobro).
    
    Args:
        telegram_id: ID del usuario de Telegram
        tier: Tier de suscripción
        trial_days: Días de prueba
    """
    expires_at = (datetime.utcnow() + timedelta(days=trial_days)).isoformat()
    set_user_subscription(telegram_id, tier, expires_at)
    
    # Otorgar créditos bonificados
    if tier == "basic":
        add_credits(telegram_id, 500, kind="trial_basic")
    elif tier == "pro":
        add_credits(telegram_id, 2000, kind="trial_pro")
    elif tier == "agency":
        add_credits(telegram_id, 5000, kind="trial_agency")
    
    logger.info(f"Trial subscription created for {telegram_id} ({tier}, {trial_days} days)")


def handle_subscription_created(subscription_id: str, stripe_customer_id: str):
    """
    Maneja el evento de suscripción creada en Stripe.
    """
    try:
        # Obtener detalles de la suscripción
        subscription = stripe.Subscription.retrieve(subscription_id)
        
        # Obtener metadata del customer
        customer = stripe.Customer.retrieve(stripe_customer_id)
        telegram_id = int(customer.metadata.get("telegram_id", 0))
        
        if not telegram_id:
            logger.error(f"No telegram_id found for customer {stripe_customer_id}")
            return
        
        # Determinar tier desde el precio
        tier = None
        for t, price_id in STRIPE_PRICES.items():
            if subscription.items.data[0].price.id == price_id:
                tier = t
                break
        
        if not tier:
            logger.error(f"Could not determine tier for subscription {subscription_id}")
            return
        
        # Calcular fecha de expiración (próxima renovación)
        expires_at = datetime.fromtimestamp(subscription.current_period_end).isoformat()
        
        # Actualizar usuario
        set_user_subscription(telegram_id, tier, expires_at)
        set_stripe_customer(telegram_id, stripe_customer_id, subscription_id)
        
        # Otorgar créditos bonificados
        credits_bonus = {
            "basic": 500,
            "pro": 2000,
            "agency": 5000
        }
        add_credits(telegram_id, credits_bonus.get(tier, 0), kind=f"subscription_{tier}")
        
        logger.info(f"Subscription {subscription_id} activated for user {telegram_id} ({tier})")
        
    except Exception as e:
        logger.error(f"Error handling subscription creation: {e}")


def handle_subscription_updated(subscription_id: str, stripe_customer_id: str):
    """
    Maneja el evento de suscripción actualizada (renovación, cambio de plan, etc).
    """
    try:
        subscription = stripe.Subscription.retrieve(subscription_id)
        
        # Si se canceló
        if subscription.status == "canceled":
            customer = stripe.Customer.retrieve(stripe_customer_id)
            telegram_id = int(customer.metadata.get("telegram_id", 0))
            
            # Revertir a free
            if telegram_id:
                set_user_subscription(telegram_id, "free")
                logger.info(f"Subscription {subscription_id} canceled for user {telegram_id}")
            return
        
        # Si está activa
        if subscription.status == "active":
            handle_subscription_created(subscription_id, stripe_customer_id)
            
    except Exception as e:
        logger.error(f"Error handling subscription update: {e}")


def handle_invoice_payment_succeeded(invoice_id: str):
    """
    Maneja el pago exitoso de una factura (renovación).
    """
    try:
        invoice = stripe.Invoice.retrieve(invoice_id)
        
        if invoice.subscription:
            subscription = stripe.Subscription.retrieve(invoice.subscription)
            handle_subscription_updated(invoice.subscription, subscription.customer)
            
    except Exception as e:
        logger.error(f"Error handling invoice payment: {e}")


def process_webhook(request):
    """
    Procesa webhooks de Stripe.
    
    Args:
        request: Flask request object
        
    Returns:
        dict: Respuesta de éxito/error
    """
    try:
        event = stripe.Webhook.construct_event(
            request.data, request.headers.get('Stripe-Signature'), WEBHOOK_SECRET
        )
    except ValueError as e:
        logger.error(f"Invalid webhook payload: {e}")
        return {"error": "Invalid payload"}, 400
    except stripe.error.SignatureVerificationError as e:
        logger.error(f"Invalid webhook signature: {e}")
        return {"error": "Invalid signature"}, 403
    
    # Handle the event
    if event["type"] == "customer.subscription.created":
        subscription = event["data"]["object"]
        handle_subscription_created(subscription["id"], subscription["customer"])
        
    elif event["type"] == "customer.subscription.updated":
        subscription = event["data"]["object"]
        handle_subscription_updated(subscription["id"], subscription["customer"])
        
    elif event["type"] == "invoice.payment_succeeded":
        invoice = event["data"]["object"]
        handle_invoice_payment_succeeded(invoice["id"])
    
    return {"success": True}, 200


def get_subscription_info(telegram_id: int) -> dict:
    """Obtiene información de suscripción de un usuario."""
    from utils.credits import get_user_subscription
    
    sub = get_user_subscription(telegram_id)
    tier_info = sub["info"]
    
    return {
        "tier": sub["tier"],
        "name": tier_info.get("name"),
        "price": tier_info.get("price"),
        "features": tier_info.get("features", []),
        "daily_limit": tier_info.get("daily_limit"),
        "monthly_limit": tier_info.get("monthly_limit")
    }
