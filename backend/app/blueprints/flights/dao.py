from datetime import datetime as dt

from .models import *
from app import app
from sqlalchemy import func, extract, and_
from sqlalchemy.orm import aliased
from app.blueprints.bookings.models import Payment


def get_airports():
    return Airport.query.all()


def get_aircrafts():
    return Aircraft.query.all()


def get_routes():
    return Route.query.all()


def get_seat_classes():
    return SeatClass.query.all()


def get_airlines():
    return Airline.query.all()


def get_countries():
    return Country.query.all()


def get_flight_by_id(id):
    return Flight.query.get(id)


def get_aircraft_seat_by_id(id):
    return AircraftSeat.query.get(id)


def get_flight_seat_by_id(id):
    return FlightSeat.query.get(id)


def get_seat_class_by_id(id):
    return SeatClass.query.get(id)


def get_aircraft_by_id(id):
    return Aircraft.query.get(id)


def get_country_by_code(code):
    return Country.query.filter(Country.code.ilike(code)).first()


def get_airport_by_code(code):
    return Airport.query.filter(Airport.code.ilike(code)).first()


def get_route_by_id(id):
    return Route.query.get(id)


def get_route_by_airports(depart_airport_id, arrive_airport_id):
    return Route.query.filter_by(
        depart_airport_id=depart_airport_id, arrive_airport_id=arrive_airport_id
    ).first()


def get_max_airports():
    return Regulation.query.filter_by(key="max_airports").first().value


def get_max_stopover_airports():
    return Regulation.query.filter_by(key="max_stopover_airports").first().value


def get_min_stopover_duration():
    return Regulation.query.filter_by(key="min_stopover_duration").first().value


def get_max_stopover_duration():
    return Regulation.query.filter_by(key="max_stopover_duration").first().value


def get_min_flight_duration():
    return Regulation.query.filter_by(key="min_flight_duration").first().value


def get_max_flight_duration():
    return Regulation.query.filter_by(key="max_flight_duration").first().value


def get_customer_min_booking_time():
    return Regulation.query.filter_by(key="customer_min_booking_time").first().value


def get_staff_min_booking_time():
    return Regulation.query.filter_by(key="staff_min_booking_time").first().value


def get_airport_number():
    return Airport.query.count()


def add_route(depart_airport_id, arrive_airport_id):
    # Tạo đối tượng Route mới
    new_route = Route(
        depart_airport_id=depart_airport_id,
        arrive_airport_id=arrive_airport_id,
    )

    # Thêm vào session của SQLAlchemy
    db.session.add(new_route)

    try:
        # commit dữ liệu vào cơ sở dữ liệu
        db.session.commit()
        print("New route added successfully!")
        return new_route
    except Exception as e:
        # Rollback nếu có lỗi xảy ra
        db.session.rollback()
        print(f"Failed to add new route: {e}")
        return None


def add_flight(
    route_id,
    code,
    depart_time: dt,
    arrive_time: dt,
    aircraft_id,
):
    new_flight = Flight(
        route_id=route_id,
        code=code,
        depart_time=depart_time,
        arrive_time=arrive_time,
        aircraft_id=aircraft_id,
    )

    db.session.add(new_flight)

    try:
        # commit dữ liệu vào cơ sở dữ liệu
        db.session.commit()
        return new_flight
    except Exception as e:
        print(f"Failed to add new flight: {e}")
        db.session.rollback()
        return None


def add_stopover(airport_id, flight_id, arrival_time, departure_time, order, note):
    stopover = Stopover(
        airport_id=airport_id,
        flight_id=flight_id,
        arrival_time=arrival_time,
        departure_time=departure_time,
        order=order,
        note=note,
    )

    db.session.add(stopover)
    return stopover


def load_flights(page=None, route_id=None):
    query = Flight.query
    query = query.filter(Flight.route_id == route_id)
    query = query.order_by(Flight.id.desc())

    page_size = app.config["PAGE_SIZE"]
    start = (page - 1) * page_size
    query = query.slice(start, start + page_size)

    return query.all()


def find_intermediate_airport(flight_id):
    # Tìm tất cả sân bay trung gian của một chuyến bay cụ thể
    intermediate_airports = Stopover.query.filter(Stopover.flight_id == flight_id).all()
    # Trả về kết quả dưới dạng danh sách dictionary
    return [
        intermediate_airport.to_dict() for intermediate_airport in intermediate_airports
    ]


def add_aircraft(name, airline_id, seat_data: dict):
    """
    Add a new aircraft to the database along with its seats
    seat_data: dict of seat class id and number of seats
    """
    new_aircraft = Aircraft(name=name, airline_id=airline_id)
    count = 1
    for seat_class_id, seat_num in seat_data.items():
        for _ in range(seat_num):
            new_aircraft.seats.append(
                AircraftSeat(seat_class_id=seat_class_id, seat_name=f"S{count:03d}")
            )
            count += 1

    db.session.add(new_aircraft)
    db.session.commit()
    return new_aircraft


def get_flights_by_route_and_date(
    route_id, depart_date, page=1, per_page=app.config["PAGE_SIZE"]
):
    route = get_route_by_id(route_id)
    if not route:
        return None
    if not route.flights:
        return None
    return Flight.query.filter(
        Flight.route_id == route_id,
        db.func.date(Flight.depart_time) == depart_date,
    ).paginate(page=page, per_page=per_page)


def add_flight_seat(flight_id, aircraft_seat_id, price, currency="VND"):
    new_flight_seat = FlightSeat(
        flight_id=flight_id,
        aircraft_seat_id=aircraft_seat_id,
        price=price,
        currency=currency,
    )

    db.session.add(new_flight_seat)
    return new_flight_seat


def revenue_sum(list):
    sum = 0
    for l in list:
        sum += l[-1]
    return sum


def revenue_stats_route_by_time(year=None, month=None):
    AirportDepart = aliased(Airport)
    AirportArrive = aliased(Airport)

    return (
        db.session.query(
            func.concat(AirportDepart.name, " - ", AirportArrive.name),
            func.count(Flight.id.distinct()),
            func.sum(Payment.amount),
        )
        .join(Reservation, Reservation.id == Payment.reservation_id)
        .join(FlightSeat, FlightSeat.id == Reservation.flight_seat_id)
        .join(Flight, Flight.id == FlightSeat.flight_id)
        .join(Route, Route.id == Flight.route_id)
        .join(AirportDepart, AirportDepart.id == Route.depart_airport_id)
        .join(AirportArrive, AirportArrive.id == Route.arrive_airport_id)
        .filter(
            func.extract("year", Payment.created_at) == year,
            func.extract("month", Payment.created_at) == month,
        )
        .group_by(AirportDepart.name, AirportArrive.name)
        .all()
    )
