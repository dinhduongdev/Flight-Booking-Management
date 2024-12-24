from datetime import datetime as dt

from .models import *
from app import app
from sqlalchemy import func, extract
from sqlalchemy.orm import aliased

def get_airports():
    return Airport.query.all()


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


def get_flight_seat_by_id(id):
    return FlightSeat.query.get(id)


def get_flight_seat_of_flight(flight: Flight, flight_seat_id: int):
    return next((fs for fs in flight.seats if fs.id == flight_seat_id), None)


def get_seat_class_by_id(id):
    return SeatClass.query.get(id)


def get_aircraft_by_id(id):
    return Aircraft.query.get(id)

def get_aircraft_seats_by_aircraft(aircraft_id):
    return AircraftSeat.query.filter(AircraftSeat.aircraft_id == aircraft_id).all()


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
    depart_time: dt,
    arrive_time: dt,
    aircraft_id,
):
    if depart_time >= arrive_time:
        raise ValueError("Depart time must be less than arrive time")
    # Check flight duration
    flight_minutes = (arrive_time - depart_time).seconds // 60
    min_f_duration = get_min_flight_duration()
    max_f_duration = get_max_flight_duration()
    if not min_f_duration <= flight_minutes <= max_f_duration:
        raise ValueError(
            f"Flight duration must be between {min_f_duration} - {max_f_duration} minutes!"
        )

    new_flight = Flight(
        route_id=route_id,
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
        db.session.rollback()
        return None


def add_intermediate_airport(
    airport_id, flight_id, arrival_time, departure_time, order, note
):
    new_intermediate_airport = Stopover(
        airport_id=airport_id,
        flight_id=flight_id,
        arrival_time=arrival_time,
        departure_time=departure_time,
        order=order,
        note=note
    )

    db.session.add(new_intermediate_airport)

    try:
        db.session.commit()
        return new_intermediate_airport
    except Exception as e:
        db.session.rollback()
        return None


def load_routes(kw_depart_airport=None, kw_arrive_airport=None, page=None):
    query = Route.query
    if kw_depart_airport:
        query = query.filter(Route.depart_airport_id == int(kw_depart_airport))

    if kw_arrive_airport:
        query = query.filter(Route.arrive_airport_id == int(kw_arrive_airport))

    page_size = app.config["PAGE_SIZE"]
    start = (page - 1) * page_size
    query = query.slice(start, start + page_size)

    return query.all()


def get_country_by_code(code):
    return Country.query.filter(Country.code.ilike(code)).first()


def get_airport_by_code(code):
    return Airport.query.filter(Airport.code.ilike(code)).first()


def get_route_by_airports(depart_airport_id, arrive_airport_id):
    return Route.query.filter_by(
        depart_airport_id=depart_airport_id, arrive_airport_id=arrive_airport_id
    ).first()


def count_routes(kw_depart_airport=None, kw_arrive_airport=None):
    query = Route.query
    if kw_depart_airport and kw_arrive_airport:
        return query.filter(
            Route.depart_airport_id == int(kw_depart_airport),
            Route.arrive_airport_id == int(kw_arrive_airport),
        ).count()
    elif kw_depart_airport:
        return query.filter(Route.depart_airport_id == int(kw_depart_airport)).count()
    elif kw_arrive_airport:
        return query.filter(Route.arrive_airport_id == int(kw_arrive_airport)).count()

    return Route.query.count()


def get_route_by_id(id):
    return Route.query.get(id)


# not stopover airport
def load_stopover_airport():
    return Airport.query.all()


def load_airports(id_depart_airport=None, id_arrive_airport=None):
    return Airport.query.filter(
        Airport.id != id_depart_airport, Airport.id != id_arrive_airport
    ).all()


def load_flights(page=None, route_id=None):
    query = Flight.query
    query = query.filter(Flight.route_id == route_id)
    query = query.order_by(Flight.id.desc())

    page_size = app.config["PAGE_SIZE"]
    start = (page - 1) * page_size
    query = query.slice(start, start + page_size)

    return query.all()


def count_flights(route_id=None):
    return Flight.query.filter(Flight.route_id == route_id).count()


def find_intermediate_airport(flight_id):
    # Tìm tất cả sân bay trung gian của một chuyến bay cụ thể
    intermediate_airports = Stopover.query.filter(Stopover.flight_id == flight_id).all()
    # Trả về kết quả dưới dạng danh sách dictionary
    return [
        intermediate_airport.to_dict() for intermediate_airport in intermediate_airports
    ]


# def find_airport(kw):
#     airport_ids = [
#         airport_id[0]
#         for airport_id in Airport.query.filter(Airport.name.contains(kw))
#         .with_entities(Airport.id)
#         .all()
#     ]
#     return airport_ids


def load_aircarfts():
    return Aircraft.query.all()


def get_min_flight_duration():
    return (
        Regulation.query.filter(Regulation.key == "min_flight_duration").first().value
    )


def get_max_flight_duration():
    return (
        Regulation.query.filter(Regulation.key == "max_flight_duration").first().value
    )


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


def get_max_stopover_airports():
    return (
        Regulation.query.filter(Regulation.key == "max_stopover_airports").first().value
    )


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


def get_customer_min_booking_time():
    return (
        Regulation.query.filter(Regulation.key == "customer_min_booking_time")
        .first()
        .value
    )


def get_staff_min_booking_time():
    return (
        Regulation.query.filter(Regulation.key == "staff_min_booking_time")
        .first()
        .value
    )


def get_min_stopover_duration():
    return (
        Regulation.query.filter(Regulation.key == "min_stopover_duration").first().value
    )


def get_max_stopover_duration():
    return (
        Regulation.query.filter(Regulation.key == "max_stopover_duration").first().value
    )

def add_flight_seat(flight_id, aircraft_seat_id, price, currency):
    new_flight_seat = FlightSeat(
        flight_id=flight_id,
        aircraft_seat_id=aircraft_seat_id,
        price=price,
        currency=currency
    )

    db.session.add(new_flight_seat)

    try:
        db.session.commit()
        return new_flight_seat
    except Exception as e:
        db.session.rollback()
        return None
    

def get_flight_count_by_route(year, month):
    depart_airport = aliased(Airport)
    arrive_airport = aliased(Airport)
    
    # Lọc theo năm và tháng
    stats = db.session.query(
            depart_airport.name.label('depart_airport_name'),
            arrive_airport.name.label('arrive_airport_name'),
            func.count(Flight.id).label('flight_count')
        )\
        .join(Route, Route.id == Flight.route_id)\
        .join(depart_airport, depart_airport.id == Route.depart_airport_id)\
        .join(arrive_airport, arrive_airport.id == Route.arrive_airport_id)\
        .filter(
            extract('year', Flight.depart_time) == year, 
            extract('month', Flight.depart_time) == month  
        )\
        .group_by(depart_airport.name, arrive_airport.name)\
        .all()
    
    total_flights = sum(s.flight_count for s in stats)
    
    result = []
    for s in stats:
        ti_le = (s.flight_count / total_flights) * 100 if total_flights > 0 else 0
        result.append({
            'depart_airport_name': s.depart_airport_name,
            'arrive_airport_name': s.arrive_airport_name,
            'flight_count': s.flight_count,
            'ti_le': round(ti_le, 2)  
        })

    return result