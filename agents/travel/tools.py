"""
Voyager - Travel booking concierge tools.

Demonstrates all three HITL patterns in Agno, anchored to one real booking task:
1. requires_user_input    - Traveler supplies the values only they can (flight, seat, passenger name)
2. requires_confirmation  - Operator approves before money is spent on the booking
3. external_execution     - Live fare is pulled from the airline's pricing service (check_live_fare)

All tools return simulated responses for demo purposes. Flight search returns a
small, stable set of options so the rest of the flow has something concrete to act on.
"""

from agno.tools import tool

# A small, deterministic catalogue so search results are stable across a session.
_CARRIERS = ["SkyLine", "AeroNova", "BlueJet"]


@tool
def search_flights(origin: str, destination: str, date: str) -> str:
    """Search for available flights between two cities on a date.

    Args:
        origin: Departure city or airport (e.g. 'San Francisco' or 'SFO').
        destination: Arrival city or airport (e.g. 'New York' or 'JFK').
        date: Travel date in YYYY-MM-DD format.

    Returns:
        A table of flight options with fares, each identified by a flight id.
    """
    base = abs(hash(f"{origin}{destination}{date}")) % 200
    options = []
    for i, carrier in enumerate(_CARRIERS):
        fid = f"FL-{(abs(hash(carrier + date)) % 9000) + 1000}"
        depart = f"{6 + i * 4:02d}:30"
        arrive = f"{9 + i * 4:02d}:45"
        fare = 180 + base + i * 65
        stops = "nonstop" if i < 2 else "1 stop"
        options.append((fid, carrier, depart, arrive, stops, fare))

    lines = [
        f"Flights — {origin} → {destination} on {date}:",
        "",
        "| Flight | Carrier | Depart | Arrive | Stops | Fare |",
        "|--------|---------|--------|--------|-------|------|",
    ]
    for fid, carrier, depart, arrive, stops, fare in options:
        lines.append(f"| {fid} | {carrier} | {depart} | {arrive} | {stops} | USD {fare} |")
    lines.append("")
    lines.append("Tell me which flight to book and I'll confirm your seat preference before purchasing.")
    return "\n".join(lines)


@tool(external_execution=True)
def check_live_fare(flight_id: str) -> str:
    """Pull the current live fare for a flight from the airline's pricing system.

    This runs outside the agent, against the live fares service (external execution) — fares
    move in real time, so the up-to-the-second price comes from the airline, not the agent.

    Args:
        flight_id: The flight to re-price (e.g. 'FL-4821').

    Returns:
        The current live fare for the flight.
    """
    fare = 180 + (abs(hash(flight_id)) % 240)
    return f"Live fare for {flight_id}: USD {fare} (held for 10 minutes)."


@tool(
    requires_user_input=True,
    user_input_fields=["flight_id", "seat_preference", "passenger_name"],
)
def select_flight_details(flight_id: str = "", seat_preference: str = "", passenger_name: str = "") -> str:
    """Collect the traveler's booking details. Prompts for the values only the traveler can provide.

    All three fields are gathered through a single human-in-the-loop prompt rather than chat
    questions: which flight, the seat preference, and the passenger name on the ticket.

    Args:
        flight_id: The flight the traveler chose (e.g. 'FL-4821').
        seat_preference: window, aisle, middle, or extra-legroom.
        passenger_name: Full name exactly as it should appear on the ticket.

    Returns:
        The assigned seat and the details to confirm before booking.
    """
    pref = (seat_preference or "any").lower()
    row = (abs(hash(flight_id)) % 28) + 6
    letter = {"window": "A", "aisle": "C", "middle": "B", "extra-legroom": "D"}.get(pref, "A")
    seat = f"{row}{letter}"
    return (
        f"Booking details captured for {flight_id}:\n"
        f"  Passenger: {passenger_name or '(not provided)'}\n"
        f"  Seat preference: {seat_preference or 'no preference'}\n"
        f"  Seat: {seat}\n"
        f"  Next: I'll confirm with you before purchasing the ticket."
    )


@tool(requires_confirmation=True)
def book_flight(flight_id: str, passenger_name: str, fare_usd: float) -> str:
    """Book a flight and hold the reservation. Requires traveler confirmation before purchasing.

    Args:
        flight_id: The flight to book (e.g. 'FL-4821').
        passenger_name: Name the ticket is issued to.
        fare_usd: The fare to be charged, in USD.

    Returns:
        A held booking reference, pending payment.
    """
    booking_ref = f"BK-{abs(hash(flight_id + passenger_name)) % 100000:05d}"
    return (
        f"Booking held (payment pending):\n"
        f"  Reference: {booking_ref}\n"
        f"  Flight: {flight_id}\n"
        f"  Passenger: {passenger_name}\n"
        f"  Fare: USD {fare_usd:,.2f}\n"
        f"  Next: the card charge runs securely in the payment service to issue the ticket."
    )


@tool
def charge_payment(booking_ref: str, amount_usd: float) -> str:
    """Charge the traveler's saved card to issue the ticket and confirm the booking.

    Args:
        booking_ref: The held booking reference to charge (e.g. 'BK-04821').
        amount_usd: Amount to charge, in USD.

    Returns:
        Payment status and the issued ticket number.
    """
    ticket = f"TKT-{abs(hash(booking_ref)) % 1000000:06d}"
    return (
        f"Payment captured for {booking_ref}:\n"
        f"  Amount: USD {amount_usd:,.2f}\n"
        f"  Ticket issued: {ticket}\n"
        f"  Status: confirmed — itinerary emailed to the traveler"
    )
