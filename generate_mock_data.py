import pandas as pd
import random
from faker import Faker

fake = Faker('pl_PL')
random.seed(42)

num_users = 10000
users_data = []
for i in range(1, num_users+1):
    users_data.append({
        'user_id': i,
        'user_name': fake.user_name(),
        'age': fake.random_int(18, 70),
        'gender': fake.random_element(elements=('M', 'F')),
        'country': random.choice(["Poland", "Germany", "Ukraine", "Czech Republic", "Slovakia", "Lithuania"]),
        'registration_date': fake.date_between(start_date='-2y', end_date='today'),
        'premium': random.choice([True, False])
    })
df_users = pd.DataFrame(users_data)
df_users.to_csv('users_data.csv', index=False)

num_products = 1000
categories = ["Electronics", "Apparel", "Home and Garden", "Books and Entertainment", "Sports and Outdoors", "Cosmetics"]
brands = {
    "Electronics": ["Samsung", "Apple", "Sony", "Xiaomi", "Asus", "Lenovo", "Philips", "LG"],
    "Apparel": ["Nike", "Adidas", "Zara", "H&M", "Levi's", "Puma", "Calvin Klein", "Tommy Hilfiger"],
    "Home and Garden": ["IKEA", "Bosch", "Tefal", "Black&Decker", "Bricomarche", "Karcher", "Philips"],
    "Books and Entertainment": ["PWN", "Znak", "Empik Go", "Netflix", "Sony Interactive", "Ubisoft", "LEGO"],
    "Sports and Outdoors": ["Decathlon", "4F", "The North Face", "Salomon", "Quechua", "Kross"],
    "Cosmetics": ["L'Oreal", "Nivea", "Ziaja", "Rossmann", "Gillette", "Eveline", "Bioderma"]
}
country_category_weights = {
    "Poland":   [40, 10, 20, 10, 10, 10],   # główna: Elektronika, druga: Dom i Ogrod
    "Germany":   [10, 40, 10, 10, 20, 10],   # główna: Odziez, druga: Sport i Turystyka
    "Lithuania":    [10, 10, 10, 10, 40, 20],   # główna: Sport i Turystyka, druga: Kosmetyki
    "Ukraine":  [10, 10, 40, 20, 10, 10],   # główna: Dom i Ogrod, druga: Ksiazki i Rozrywka
    "Czech Republic":   [20, 10, 10, 40, 10, 10],   # główna: Ksiazki i Rozrywka, druga: Elektronika
    "Slovakia": [10, 20, 10, 10, 10, 40],   # główna: Kosmetyki, druga: Odziez
}
products_data = []
for i in range(1, num_products + 1):
    chosen_category = random.choice(categories)
    chosen_brand = random.choice(brands[chosen_category])
    products_data.append({
        'product_id': i,
        'category': chosen_category,
        'brand': chosen_brand,
        'price': round(random.uniform(10.0, 6000.0), 2),
        'rating': round(random.uniform(1.0, 5.0), 1),
        'stock': random.randint(0, 500),
        'created_at': fake.date_between(start_date='-3y', end_date='-1M').strftime("%Y-%m-%d")
    })
df_products = pd.DataFrame(products_data)
df_products.to_csv('products_data.csv', index=False)

num_events = 50000
event_types = ["view", "click", "add_to_cart", "purchase", "remove_from_cart", "wishlist"]
event_weights = [45, 25, 12, 6, 4, 8]
devices = ["mobile", "desktop", "laptop"]
events_data = []
products_by_category = {}
for p in products_data:
    products_by_category.setdefault(p['category'], []).append(p['product_id'])
for i in range(1, num_events + 1):
    random_user_index = random.randint(0, num_users-1)
    user = users_data[random_user_index]
    u_id = user['user_id']
    u_country = user['country']
    weights = country_category_weights[u_country]
    chosen_cat = random.choices(categories, weights=weights, k=1)[0]
    available_products = products_by_category[chosen_cat]
    p_id = random.choice(available_products)
    events_data.append({
        'event_id': i,
        'user_id': u_id,
        'product_id': p_id,
        'event_type': random.choices(event_types, weights=event_weights, k=1)[0],
        'timestamp': fake.date_time_between(start_date='-30d', end_date='now').strftime("%Y-%m-%d %H:%M:%S"),
        'session_id': f"sess_{random.randint(1, 5000)}",
        'device': random.choice(devices),
    })
df_events = pd.DataFrame(events_data)
df_events.to_csv('events_data.csv', index=False)

orders_data = []
order_counter = 1
for event in events_data:
    if event['event_type'] == "purchase":
        prod_id = event['product_id']
        product_price = next(p['price'] for p in products_data if p['product_id'] == prod_id)
        orders_data.append({
            'order_id': order_counter,
            'user_id': event['user_id'],
            'product_id': prod_id,
            'quantity': random.randint(1, 3),
            'price': product_price,
            'purchase_date': event['timestamp']
        })
        order_counter += 1
df_orders = pd.DataFrame(orders_data)
df_orders.to_csv('orders_data.csv', index=False)

campaigns = ["BlackFriday_2026", "Spring_Sale", "Influencer_Promo", "Google_Ads_Brand", "Newsletter_Welcome"]
channels = ["Social Media", "Email", "Paid Search", "Organic", "Affiliate"]
marketing_data = []
for i in range(1, 501):
    marketing_data.append({
        'campaign': random.choice(campaigns),
        'channel': random.choice(channels),
        'discount': random.choice([0.05, 0.10, 0.15, 0.20, 0.0]),
    })

df_marketing = pd.DataFrame(marketing_data)
df_marketing.to_csv('marketing_data.csv', index=False)