"""
Voyager - Travel booking concierge tools.

Demonstrates the HITL patterns in Agno, anchored to one real booking task. Structured
multiple-choice input (flight + seat) is collected via `ask_user` from UserFeedbackTools
(wired up in agent.py); these tools cover the rest:
1. requires_user_input    - Free-text fill for the passenger name when missing (set_passenger_name)
2. requires_user_input    - Recipient email for the itinerary when missing (set_recipient_email)
3. requires_confirmation  - Operator approves before the booking is held (book_flight)
4. external_execution     - Live fare is pulled from the airline's pricing service (check_live_fare)

Flight search is REAL: it queries the Duffel Flight API (offer requests) when
DUFFEL_API_TOKEN is set, and falls back to a small, deterministic catalogue otherwise
so the demo always has concrete options to act on.

Booking does NOT charge a card. Once a booking is held and confirmed, the full itinerary
is emailed to the traveler via Resend (send_email).
"""

from os import getenv

from agno.tools import tool

# Carriers used by the deterministic fallback catalogue (when DUFFEL_API_TOKEN is unset).
_CARRIERS = ["SkyLine", "AeroNova", "BlueJet"]

# Maps the friendly flight id shown to the traveler (e.g. "BA-117") to the real Duffel
# offer id (e.g. "off_0000A...") from the last search, so check_live_fare can re-price the
# actual offer. Populated by _search_duffel; a miss just means we can't live-re-price it.
_OFFER_IDS: dict[str, str] = {}

# Map common city names to IATA codes for the real Duffel search. The API needs IATA
# codes; if a value already looks like a 3-letter code we pass it through unchanged.
_CITY_TO_IATA = {
    "san francisco": "SFO",
    "new york": "JFK",
    "los angeles": "LAX",
    "chicago": "ORD",
    "miami": "MIA",
    "boston": "BOS",
    "seattle": "SEA",
    "london": "LHR",
    "paris": "CDG",
    "tokyo": "HND",
}


def _to_iata(place: str) -> str:
    """Resolve a city name to an IATA code; pass through anything that already looks like one."""
    p = place.strip()
    if len(p) == 3 and p.isalpha():
        return p.upper()
    return _CITY_TO_IATA.get(p.lower(), p[:3].upper())


def _flight_id(carrier: str, date: str) -> str:
    """Stable, demo-friendly flight id (FL-####) the rest of the flow can refer to."""
    return f"FL-{(abs(hash(carrier + date)) % 9000) + 1000}"


def _render_table(origin: str, destination: str, date: str, options: list[tuple]) -> str:
    """Render flight options as the Markdown table the agent presents to the traveler."""
    lines = [
        f"Flights — {origin} → {destination} on {date}:",
        "",
        "| Flight | Carrier | Depart | Arrive | Stops | Fare |",
        "|--------|---------|--------|--------|-------|------|",
    ]
    for fid, carrier, depart, arrive, stops, fare, currency in options:
        lines.append(f"| {fid} | {carrier} | {depart} | {arrive} | {stops} | {currency} {fare} |")
    lines.append("")
    lines.append("Tell me which flight to book and I'll confirm your seat preference before purchasing.")
    return "\n".join(lines)


def _search_duffel(origin: str, destination: str, date: str) -> list[tuple] | None:
    """Query the Duffel Flight API (offer requests). Returns option tuples, or None to fall back.

    Each tuple is (flight_id, carrier, depart, arrive, stops, fare, currency). Returns None
    when the token is unset or the call fails, so the caller can fall back to sample data.
    """
    token = getenv("DUFFEL_API_TOKEN")
    if not token:
        return None

    import requests

    try:
        response = requests.post(
            "https://api.duffel.com/air/offer_requests",
            params={"return_offers": "true"},
            headers={
                "Authorization": f"Bearer {token}",
                "Duffel-Version": "v2",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            json={
                "data": {
                    "slices": [
                        {"origin": _to_iata(origin), "destination": _to_iata(destination), "departure_date": date}
                    ],
                    "passengers": [{"type": "adult"}],
                    "cabin_class": "economy",
                }
            },
            timeout=30,
        )
        response.raise_for_status()
        offers = (response.json().get("data", {}).get("offers") or [])[:5]
    except Exception:  # noqa: BLE001 - any API/network failure → fall back to sample data
        return None

    options: list[tuple] = []
    for offer in offers:
        try:
            segments = offer["slices"][0]["segments"]
            first, last = segments[0], segments[-1]
            carrier = first.get("marketing_carrier") or {}
            carrier_name = carrier.get("name") or carrier.get("iata_code") or "Airline"
            iata = carrier.get("iata_code") or ""
            flight_no = first.get("marketing_carrier_flight_number") or ""
            fid = f"{iata}-{flight_no}" if iata and flight_no else _flight_id(carrier_name, date)
            depart = first["departing_at"][11:16]
            arrive = last["arriving_at"][11:16]
            stops = "nonstop" if len(segments) == 1 else f"{len(segments) - 1} stop"
            fare = f"{float(offer['total_amount']):.0f}"
            currency = offer.get("total_currency") or "USD"
            # Remember the real Duffel offer id so check_live_fare can re-price this flight.
            offer_id = offer.get("id")
            if offer_id:
                _OFFER_IDS[fid] = offer_id
            options.append((fid, carrier_name, depart, arrive, stops, fare, currency))
        except (KeyError, IndexError, ValueError, TypeError):
            continue

    return options or None


def _search_fallback(origin: str, destination: str, date: str) -> list[tuple]:
    """Deterministic sample catalogue used when Duffel is unavailable."""
    base = abs(hash(f"{origin}{destination}{date}")) % 200
    options: list[tuple] = []
    for i, carrier in enumerate(_CARRIERS):
        fid = _flight_id(carrier, date)
        depart = f"{6 + i * 4:02d}:30"
        arrive = f"{9 + i * 4:02d}:45"
        fare = str(180 + base + i * 65)
        stops = "nonstop" if i < 2 else "1 stop"
        options.append((fid, carrier, depart, arrive, stops, fare, "USD"))
    return options


@tool
def search_flights(origin: str, destination: str, date: str) -> str:
    """Search for available flights between two cities on a date.

    Uses the Duffel live flight-offers service when configured, otherwise a stable sample set.

    Args:
        origin: Departure city or airport (e.g. 'San Francisco' or 'SFO').
        destination: Arrival city or airport (e.g. 'New York' or 'JFK').
        date: Travel date in YYYY-MM-DD format.

    Returns:
        A table of flight options with fares, each identified by a flight id.
    """
    options = _search_duffel(origin, destination, date) or _search_fallback(origin, destination, date)
    return _render_table(origin, destination, date, options)


def _reprice_duffel(flight_id: str) -> str | None:
    """Re-price a flight via Duffel's Get-Offer endpoint. Returns a message, or None to fall back.

    Looks up the real Duffel offer id captured during search, then calls GET /air/offers/{id}
    for the up-to-the-second price and expiry. Returns None when there's no token or no cached
    offer id (e.g. the flight came from the sample catalogue), so the caller can fall back.
    """
    token = getenv("DUFFEL_API_TOKEN")
    offer_id = _OFFER_IDS.get(flight_id)
    if not (token and offer_id):
        return None

    import requests

    try:
        response = requests.get(
            f"https://api.duffel.com/air/offers/{offer_id}",
            headers={
                "Authorization": f"Bearer {token}",
                "Duffel-Version": "v2",
                "Accept": "application/json",
            },
            timeout=30,
        )
        response.raise_for_status()
        offer = response.json().get("data") or {}
        fare = f"{float(offer['total_amount']):.2f}"
        currency = offer.get("total_currency") or "USD"
    except Exception:  # noqa: BLE001 - any API/network failure → fall back to sample re-price
        return None

    expires = offer.get("expires_at")
    held = f" (held until {expires[11:16]} UTC)" if expires and len(expires) >= 16 else ""
    return f"Live fare for {flight_id}: {currency} {fare}{held}."


@tool(external_execution=True)
def check_live_fare(flight_id: str) -> str:
    """Pull the current live fare for a flight from the airline's pricing system.

    This runs outside the agent, against the live fares service (external execution) — fares
    move in real time, so the up-to-the-second price comes from the airline (Duffel), not the
    agent. Falls back to a stable estimate when the flight isn't a live Duffel offer.

    Args:
        flight_id: The flight to re-price (e.g. 'BA-117'), as shown by search_flights.

    Returns:
        The current live fare for the flight.
    """
    real = _reprice_duffel(flight_id)
    if real is not None:
        return real
    fare = 180 + (abs(hash(flight_id)) % 240)
    return f"Live fare for {flight_id}: USD {fare} (estimated)."


@tool(requires_user_input=True, user_input_fields=["passenger_name"])
def set_passenger_name(passenger_name: str = "") -> str:
    """Ask the traveler for the passenger name (free text) when it wasn't already provided.

    Only use this when no name has been given in the conversation — it pauses and prompts the
    traveler to type the name exactly as it should appear on the ticket.

    Args:
        passenger_name: Full name for the ticket.

    Returns:
        Confirmation of the captured name.
    """
    return f"Passenger name set to: {passenger_name or '(not provided)'}"


@tool(requires_user_input=True, user_input_fields=["recipient_email"])
def set_recipient_email(recipient_email: str = "") -> str:
    """Ask the traveler for the email address the itinerary should be sent to.

    Use this when no email has been given in the conversation — it pauses and prompts the
    traveler to type the address where they want the confirmed itinerary delivered.

    Args:
        recipient_email: Email address for the itinerary.

    Returns:
        Confirmation of the captured email address.
    """
    return f"Itinerary will be sent to: {recipient_email or '(not provided)'}"


@tool(requires_confirmation=True)
def book_flight(flight_id: str, passenger_name: str, fare_usd: float, seat_preference: str = "") -> str:
    """Confirm the booking and assign a seat. Requires traveler confirmation before booking.

    Search and live fares are real (Duffel); placing a real airline order requires full
    passenger/payment details, so this step records a held reservation reference rather than
    issuing a real PNR. The confirmed details are what gets emailed to the traveler.

    Args:
        flight_id: The flight to book (e.g. 'BA-117').
        passenger_name: Name the ticket is issued to.
        fare_usd: The fare for the booking, in USD.
        seat_preference: Seat choice the traveler picked (window, aisle, middle, or extra-legroom).

    Returns:
        A confirmed booking reference, ready to be emailed to the traveler.
    """
    pref = (seat_preference or "any").lower()
    row = (abs(hash(flight_id)) % 28) + 6
    letter = {"window": "A", "aisle": "C", "middle": "B", "extra-legroom": "D"}.get(pref, "A")
    seat = f"{row}{letter}"
    booking_ref = f"BK-{abs(hash(flight_id + passenger_name)) % 100000:05d}"
    return (
        f"Booking confirmed:\n"
        f"  Reference: {booking_ref}\n"
        f"  Flight: {flight_id}\n"
        f"  Passenger: {passenger_name}\n"
        f"  Seat: {seat} ({seat_preference or 'no preference'})\n"
        f"  Fare: USD {fare_usd:,.2f}\n"
        f"  Next: I'll email the full itinerary to the traveler."
    )
