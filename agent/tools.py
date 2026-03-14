import sqlite3
import json
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "restaurants.db")

def get_connection():
    return sqlite3.connect(DB_PATH)

def search_restaurants(location: str = None, cuisine: str = None, min_capacity: int = None):
    """Searches for restaurants based on location, cuisine, and minimum party size capacity."""
    conn = get_connection()
    cursor = conn.cursor()
    
    query = "SELECT id, name, location, cuisine, rating, price_tier, capacity, description FROM restaurants WHERE 1=1"
    params = []
    
    if location:
        query += " AND location LIKE ?"
        params.append(f"%{location}%")
    if cuisine:
        query += " AND cuisine LIKE ?"
        params.append(f"%{cuisine}%")
    if min_capacity:
        query += " AND capacity >= ?"
        params.append(min_capacity)
        
    query += " ORDER BY rating DESC LIMIT 5"
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    
    if not rows:
        return json.dumps({"status": "success", "message": "No restaurants found matching those criteria.", "results": []})
        
    results = [
        {
            "id": r[0],
            "name": r[1],
            "location": r[2],
            "cuisine": r[3],
            "rating": r[4],
            "price_tier": r[5],
            "capacity": r[6],
            "description": r[7]
        }
        for r in rows
    ]
    return json.dumps({"status": "success", "results": results})

def check_availability(restaurant_id: int, date: str, time: str, party_size: int):
    """Checks if a restaurant has capacity for a specific party size at a given date and time."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Get restaurant total capacity
    cursor.execute("SELECT capacity, name FROM restaurants WHERE id = ?", (restaurant_id,))
    res = cursor.fetchone()
    if not res:
        conn.close()
        return json.dumps({"status": "error", "message": f"Restaurant with ID {restaurant_id} not found."})
        
    total_capacity, name = res
    
    # Get existing reservations for that slot
    cursor.execute("""
        SELECT SUM(party_size) FROM reservations 
        WHERE restaurant_id = ? AND date = ? AND time = ? AND status = 'CONFIRMED'
    """, (restaurant_id, date, time))
    
    booked = cursor.fetchone()[0] or 0
    available_seats = total_capacity - booked
    conn.close()
    
    is_available = available_seats >= party_size
    
    return json.dumps({
        "status": "success",
        "restaurant_name": name,
        "date": date,
        "time": time,
        "party_size": party_size,
        "is_available": is_available,
        "available_seats": available_seats
    })

def book_reservation(restaurant_id: int, date: str, time: str, party_size: int, customer_name: str, customer_email: str):
    """Books a reservation if capacity allows."""
    # First check availability
    avail_check = json.loads(check_availability(restaurant_id, date, time, party_size))
    if avail_check.get("status") == "error":
        return json.dumps(avail_check)
        
    if not avail_check.get("is_available"):
        return json.dumps({
            "status": "error", 
            "message": f"Insufficient capacity. Only {avail_check.get('available_seats')} seats left."
        })
        
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO reservations (restaurant_id, customer_name, customer_email, date, time, party_size, status)
            VALUES (?, ?, ?, ?, ?, ?, 'CONFIRMED')
        """, (restaurant_id, customer_name, customer_email, date, time, party_size))
        
        reservation_id = cursor.lastrowid
        conn.commit()
    except Exception as e:
        conn.rollback()
        return json.dumps({"status": "error", "message": str(e)})
    finally:
        conn.close()
        
    return json.dumps({
        "status": "success",
        "message": "Reservation confirmed.",
        "reservation_id": reservation_id,
        "restaurant_name": avail_check.get("restaurant_name"),
        "date": date,
        "time": time,
        "party_size": party_size
    })

def cancel_reservation(reservation_id: int):
    """Cancels a reservation by its ID."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT status FROM reservations WHERE id = ?", (reservation_id,))
    res = cursor.fetchone()
    if not res:
        conn.close()
        return json.dumps({"status": "error", "message": f"Reservation ID {reservation_id} not found."})
        
    if res[0] == 'CANCELLED':
        conn.close()
        return json.dumps({"status": "error", "message": f"Reservation {reservation_id} is already cancelled."})
        
    cursor.execute("UPDATE reservations SET status = 'CANCELLED' WHERE id = ?", (reservation_id,))
    conn.commit()
    conn.close()
    
    return json.dumps({
        "status": "success",
        "message": f"Reservation {reservation_id} successfully cancelled."
    })


def get_tool_schemas():
    """Returns the JSON schema definitions for the tools."""
    return [
        {
            "type": "function",
            "function": {
                "name": "search_restaurants",
                "description": "Searches for restaurants based on criteria like location, cuisine, or party size capacity.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {"type": "string", "description": "The neighborhood or area, e.g., 'Downtown', 'Midtown'."},
                        "cuisine": {"type": "string", "description": "The type of food, e.g., 'Italian', 'Vegan'."},
                        "min_capacity": {"type": "integer", "description": "Minimum party size the restaurant must accommodate."}
                    }
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "check_availability",
                "description": "Checks if a specific restaurant has open tables for a given date, time, and party size.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "restaurant_id": {"type": "integer", "description": "The ID of the restaurant (found via search_restaurants)."},
                        "date": {"type": "string", "description": "The date in YYYY-MM-DD format."},
                        "time": {"type": "string", "description": "The time in HH:MM format, e.g., '18:30'."},
                        "party_size": {"type": "integer", "description": "Number of people in the party."}
                    },
                    "required": ["restaurant_id", "date", "time", "party_size"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "book_reservation",
                "description": "Books a reservation at a restaurant. ALWAYS run check_availability first.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "restaurant_id": {"type": "integer", "description": "The ID of the restaurant."},
                        "date": {"type": "string", "description": "The date in YYYY-MM-DD format."},
                        "time": {"type": "string", "description": "The time in HH:MM format."},
                        "party_size": {"type": "integer", "description": "Number of people in the party."},
                        "customer_name": {"type": "string", "description": "Name of the customer."},
                        "customer_email": {"type": "string", "description": "Email address of the customer."}
                    },
                    "required": ["restaurant_id", "date", "time", "party_size", "customer_name", "customer_email"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "cancel_reservation",
                "description": "Cancels an existing reservation using the reservation ID.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "reservation_id": {"type": "integer", "description": "The ID of the reservation to cancel."}
                    },
                    "required": ["reservation_id"]
                }
            }
        }
    ]

# Mapping string names to the actual python functions for the agent core
available_functions = {
    "search_restaurants": search_restaurants,
    "check_availability": check_availability,
    "book_reservation": book_reservation,
    "cancel_reservation": cancel_reservation
}
