import sqlite3
import random
import os
from datetime import datetime, timedelta

def create_database(db_path="data/restaurants.db"):
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Drop existing tables if they exist
    cursor.execute("DROP TABLE IF EXISTS reservations")
    cursor.execute("DROP TABLE IF EXISTS restaurants")

    # Create restaurants table
    cursor.execute('''
        CREATE TABLE restaurants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            location TEXT NOT NULL,
            cuisine TEXT NOT NULL,
            rating REAL NOT NULL,
            price_tier TEXT NOT NULL,
            capacity INTEGER NOT NULL,
            description TEXT NOT NULL
        )
    ''')

    # Create reservations table
    cursor.execute('''
        CREATE TABLE reservations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            restaurant_id INTEGER NOT NULL,
            customer_name TEXT NOT NULL,
            customer_email TEXT NOT NULL,
            date TEXT NOT NULL,
            time TEXT NOT NULL,
            party_size INTEGER NOT NULL,
            status TEXT NOT NULL,
            FOREIGN KEY (restaurant_id) REFERENCES restaurants (id)
        )
    ''')

    # Seed data generator
    locations = ["Downtown", "Uptown", "Midtown", "Westside", "Eastside", "North Hills", "South Park", "Marina", "Financial District", "Arts District"]
    cuisines = ["Italian", "Japanese", "Mexican", "American", "Indian", "French", "Thai", "Vegan", "Steakhouse", "Seafood", "Mediterranean", "Korean", "Vietnamese", "Spanish Tapas"]
    adjectives = ["Rustic", "Modern", "Classic", "Urban", "Golden", "Cozy", "Grand", "Little", "Spice", "Ocean", "Green"]
    nouns = ["Spoon", "Fork", "Plate", "Oven", "Table", "Garden", "Kitchen", "Bistro", "Grill", "House", "Room", "Tavern", "Lounge"]

    restaurants = []
    
    # Generate 80 restaurants
    for _ in range(80):
        location = random.choice(locations)
        cuisine = random.choice(cuisines)
        name = f"GoodFoods {random.choice(adjectives)} {random.choice(nouns)} {cuisine}"
        rating = round(random.uniform(3.5, 4.9), 1)
        price_tier = random.choice(["$", "$$", "$$$", "$$$$"])
        capacity = random.choice([20, 30, 40, 50, 60, 80, 100, 150])
        description = f"A wonderful {cuisine.lower()} dining experience located in {location}. Offers a diverse menu with a {rating} star average rating."
        
        restaurants.append((name, location, cuisine, rating, price_tier, capacity, description))

    cursor.executemany('''
        INSERT INTO restaurants (name, location, cuisine, rating, price_tier, capacity, description)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', restaurants)

    # Generate some upcoming mock reservations to simulate existing bookings
    reservations = []
    # Just generate a few starting tomorrow
    today = datetime.now()
    times = ["17:00", "17:30", "18:00", "18:30", "19:00", "19:30", "20:00", "20:30", "21:00"]
    
    for _ in range(200):
        restaurant_id = random.randint(1, 80)
        days_ahead = random.randint(1, 14)
        date = (today + timedelta(days=days_ahead)).strftime("%Y-%m-%d")
        time = random.choice(times)
        party_size = random.randint(1, 8)
        status = "CONFIRMED"
        
        reservations.append((
            restaurant_id, 
            f"Customer {random.randint(1,1000)}", 
            f"customer{random.randint(1,1000)}@example.com",
            date,
            time,
            party_size,
            status
        ))

    cursor.executemany('''
        INSERT INTO reservations (restaurant_id, customer_name, customer_email, date, time, party_size, status)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', reservations)

    conn.commit()
    conn.close()
    print(f"Successfully generated 80 restaurants and 200 mock reservations in {db_path}.")

if __name__ == "__main__":
    create_database()
