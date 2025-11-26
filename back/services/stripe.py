import os
import stripe
import requests
import re

def create_checkout(reference, name, unit_price, quantity, confirmation_secret):
    """
        Create Stripe checkout
        Documentation: https://docs.stripe.com/checkout/quickstart?client=react&lang=python
    """
    
    stripe.api_key = os.getenv('STRIPE_API_KEY')
    return stripe.checkout.Session.create(
        mode='payment',
        success_url=f"http://localhost:9000/booking/{reference}?checkout_confirmation_secret={confirmation_secret}",
        cancel_url='http://localhost:9000',
        line_items=[
            {
                'quantity': quantity,
                'price_data': {
                    'currency': 'EUR',
                    'unit_amount': round(unit_price * 100),
                    'product_data': {
                        'name': name,
                    },
                },
            },
        ],
    )

def get_checkout_lines(checkout_session_id):
    # Validate checkout_session_id with regex to prevent SSRF
    if not re.match(r"^cs_(test|live)_[a-zA-Z0-9]{24,}$", checkout_session_id):
        raise ValueError("Invalid Stripe checkout session ID format.")

    url = f"https://api.stripe.com/v1/checkout/sessions/{checkout_session_id}/line_items"

    session = requests.Session()
    session.auth = (os.getenv('STRIPE_API_KEY'), "")
    return session.get(url).json()["data"]
